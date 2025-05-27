import gen.sso_pb2_grpc
from gen.sso_pb2 import LoginRequest, LoginResponse, RegisterRequest, RegisterResponse
import grpc
from ..core.db import async_engine
from sqlalchemy.ext.asyncio import AsyncSession
from ..crud import UserAuthRepository
from ..schemas import UserAuthInSchema
from pydantic import ValidationError
from ..core.security import get_password_hash, verify_password, create_access_token


class AuthServicer(gen.sso_pb2_grpc.AuthServicer):
	@staticmethod
	def set_error(context: grpc.ServicerContext, status: grpc.StatusCode, details: str):
		context.set_code(status)
		context.set_details(details)

	async def Register(self, request: RegisterRequest, context: grpc.ServicerContext) -> RegisterResponse:
		try:
			user_auth_in = UserAuthInSchema(email=request.email, password=request.password)
		except ValidationError:
			self.set_error(context, grpc.StatusCode.INVALID_ARGUMENT, 'Некорректный формат почты или пароля')
			return RegisterResponse()
		async with AsyncSession(async_engine) as async_session:
			user_auth_repository = UserAuthRepository(async_session)
			user_auth = await user_auth_repository.get_by_email(user_auth_in.email)
			if user_auth is not None:
				self.set_error(context, grpc.StatusCode.ALREADY_EXISTS,
							   'Пользователь с такой почтой уже существует')
				return RegisterResponse()
			user_auth = await user_auth_repository.create(user_auth_in.email,
														  get_password_hash(user_auth_in.password))
		return RegisterResponse(user_id=user_auth.id)

	async def Login(self, request: LoginRequest, context: grpc.ServicerContext) -> LoginResponse:
		try:
			user_auth_in = UserAuthInSchema(email=request.email, password=request.password)
		except ValidationError:
			self.set_error(context, grpc.StatusCode.INVALID_ARGUMENT, 'Некорректный формат почты или пароля')
			return LoginResponse()
		async with AsyncSession(async_engine) as async_session:
			user_auth_repository = UserAuthRepository(async_session)
			user_auth = await user_auth_repository.get_by_email(user_auth_in.email)
		if user_auth is None:
			self.set_error(context, grpc.StatusCode.INVALID_ARGUMENT,
						   'Неверная почта или пароль')
			return LoginResponse()
		if not verify_password(user_auth_in.password, user_auth.hashed_password):
			self.set_error(context, grpc.StatusCode.INVALID_ARGUMENT,
						   'Неверная почта или пароль')
			return LoginResponse()
		return LoginResponse(token=create_access_token(user_auth.email))
