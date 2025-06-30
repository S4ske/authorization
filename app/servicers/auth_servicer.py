import gen.sso_pb2_grpc
from gen.sso_pb2 import LoginRequest, TokenInfo, RegisterRequest, RegisterResponse, RefreshRequest
import grpc
from ..core.db import async_engine
from sqlalchemy.ext.asyncio import AsyncSession
from ..crud import UserAuthRepository, RefreshTokenRepository
from ..schemas import UserAuthInSchema
from pydantic import ValidationError
from ..core.security import (get_secret_hash, verify_secret_hash, create_access_token, create_refresh_token,
							 decode_jwt_token, TokenType, TOKEN_TYPE_STRING, TOKEN_SUBJECT_STRING, TOKEN_EXPIRE_STRING)
from datetime import datetime, timezone


class AuthServicer(gen.sso_pb2_grpc.AuthServicer):
	async def Register(self, request: RegisterRequest, context: grpc.ServicerContext) -> RegisterResponse:
		try:
			user_auth_in = UserAuthInSchema(email=request.email, password=request.password)
		except ValidationError:
			AuthServicer.set_incorrect_format(context)
			return RegisterResponse()
		async with AsyncSession(async_engine) as async_session:
			user_auth_repository = UserAuthRepository(async_session)
			user_auth = await user_auth_repository.get_by_email(user_auth_in.email)
			if user_auth is not None:
				AuthServicer.set_email_exist(context)
				return RegisterResponse()
			user_auth = await user_auth_repository.create(user_auth_in.email,
														  get_secret_hash(user_auth_in.password))
			id = user_auth.id
			await async_session.commit()  # TODO: Сделать нормальную обработку транзакций
			return RegisterResponse(user_id=id)

	@staticmethod
	def set_incorrect_format(context: grpc.ServicerContext) -> None:
		AuthServicer.set_response(context, grpc.StatusCode.INVALID_ARGUMENT, 'Некорректный формат почты или пароля')

	@staticmethod
	def set_response(context: grpc.ServicerContext, status: grpc.StatusCode, details: str) -> None:
		context.set_code(status)
		context.set_details(details)

	@staticmethod
	def set_email_exist(context: grpc.ServicerContext) -> None:
		AuthServicer.set_response(context, grpc.StatusCode.ALREADY_EXISTS,
								  'Пользователь с такой почтой уже существует')

	async def Login(self, request: LoginRequest, context: grpc.ServicerContext) -> TokenInfo:
		try:
			user_auth_in = UserAuthInSchema(email=request.email, password=request.password)
		except ValidationError:
			AuthServicer.set_incorrect_format(context)
			return TokenInfo()

		async with AsyncSession(async_engine) as async_session:
			user_auth_repository = UserAuthRepository(async_session)
			refresh_token_repository = RefreshTokenRepository(async_session)

			user_auth_db = await user_auth_repository.get_by_email(user_auth_in.email)
			if user_auth_db is None:
				AuthServicer.set_invalid_email_or_password(context)
				return TokenInfo()
			if not verify_secret_hash(user_auth_in.password, user_auth_db.hashed_password):
				AuthServicer.set_invalid_email_or_password(context)
				return TokenInfo()

			refresh_token = create_refresh_token(user_auth_db.email)
			await refresh_token_repository.delete_by_user_auth_id(user_auth_db.id)
			await refresh_token_repository.create_by_raw_token(refresh_token, user_auth_db.id)
			await async_session.commit()

			return TokenInfo(access_token=create_access_token(user_auth_db.email), refresh_token=refresh_token)

	@staticmethod
	def set_invalid_email_or_password(context: grpc.ServicerContext) -> None:
		AuthServicer.set_response(context, grpc.StatusCode.INVALID_ARGUMENT,
								  'Неверная почта или пароль')

	async def Refresh(self, request: RefreshRequest, context: grpc.ServicerContext) -> TokenInfo:
		refresh_token = request.refresh_token

		token_payload = decode_jwt_token(refresh_token)
		if token_payload[TOKEN_TYPE_STRING] is not TokenType.REFRESH:
			AuthServicer.set_wrong_token_type(context)
			return TokenInfo()

		async with AsyncSession(async_engine) as async_session:
			expires_at: datetime = token_payload[TOKEN_EXPIRE_STRING]
			email: str = token_payload[TOKEN_SUBJECT_STRING]
			user_auth_repository = UserAuthRepository(async_session)
			refresh_token_repository = RefreshTokenRepository(async_session)

			user_auth_db = await user_auth_repository.get_by_email(email)

			if not user_auth_db:
				AuthServicer.set_unknown_email(context)
				return TokenInfo()

			refresh_token_db = await refresh_token_repository.get(user_auth_db.id)

			if not refresh_token_db:
				AuthServicer.set_wrong_token(context)
				return TokenInfo()

			if not verify_secret_hash(refresh_token, refresh_token_db.hashed_token):
				AuthServicer.set_wrong_token(context)
				return TokenInfo()

			if datetime.now(timezone.utc) > expires_at:
				AuthServicer.set_token_expired(context)
				await refresh_token_repository.delete(refresh_token_db.id)
				return TokenInfo()

			access_token = create_access_token(email)
			new_refresh_token = create_refresh_token(email)

			await refresh_token_repository.delete(refresh_token_db.id)
			await refresh_token_repository.create_by_raw_token(new_refresh_token, user_auth_db.id)

			return TokenInfo(access_token=access_token, refresh_token=new_refresh_token)

	@staticmethod
	def set_wrong_token_type(context: grpc.ServicerContext) -> None:
		AuthServicer.set_response(context, grpc.StatusCode.INVALID_ARGUMENT,
								  'Токен не типа REFRESH')

	@staticmethod
	def set_wrong_token(context: grpc.ServicerContext) -> None:
		AuthServicer.set_response(context, grpc.StatusCode.INVALID_ARGUMENT,
						   'Неизвестный токен')

	@staticmethod
	def set_token_expired(context: grpc.ServicerContext) -> None:
		AuthServicer.set_response(context, grpc.StatusCode.INVALID_ARGUMENT,
								  'Время действия токена истекло')

	@staticmethod
	def set_unknown_email(context: grpc.ServicerContext) -> None:
		AuthServicer.set_response(context, grpc.StatusCode.INVALID_ARGUMENT,
								  'Нет пользователя с такой почтой')
