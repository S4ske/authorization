from sqlalchemy.ext.asyncio import AsyncSession
from ..models import UserAuth, RefreshToken
from sqlalchemy import select
from typing import Any
from ..core.security import (TOKEN_TYPE_STRING, TokenType, get_secret_hash, TOKEN_EXPIRE_STRING, TOKEN_SUBJECT_STRING,
							 decode_jwt_token)
from sqlalchemy.orm import Mapped


class RefreshTokenRepository:
	def __init__(self, async_session: AsyncSession):
		self._async_session = async_session

	async def create_by_raw_token(self, refresh_token: str, user_auth_id: int | None = None) -> RefreshToken:
		token_payload: dict[str, Any] = decode_jwt_token(refresh_token)
		if token_payload[TOKEN_TYPE_STRING] is not TokenType.REFRESH:
			raise ValueError('Token is not a refresh')
		if user_auth_id is None:
			user_auth_id = (await self._get_user_auth(token_payload[TOKEN_SUBJECT_STRING])).id
		refresh_token_db = RefreshToken(hashed_token=get_secret_hash(refresh_token),
										expires_at=token_payload[TOKEN_EXPIRE_STRING],
										user_auth_id=user_auth_id)
		self._async_session.add(refresh_token_db)
		await self._async_session.flush()
		await self._async_session.refresh(refresh_token_db)
		return refresh_token_db

	async def _get_user_auth(self, email: str) -> UserAuth | None:
		stmt = select(UserAuth).where(UserAuth.email == email)
		result = await self._async_session.execute(stmt)
		if not result:
			return None
		user_auth = result.first()
		if not user_auth:
			return None
		return user_auth[0]

	async def get_by_user_auth_id(self, user_auth_id: int) -> RefreshToken | None:
		return await self._get(RefreshToken.user_auth_id, user_auth_id)

	async def get(self, id: int) -> RefreshToken | None:
		return await self._get(RefreshToken.id, id)

	async def _get(self, field: Mapped, value: Any) -> RefreshToken | None:
		stmt = select(UserAuth).where(field == value)
		result = await self._async_session.execute(stmt)
		if not result:
			return None
		refresh_token_row = result.first()
		if not refresh_token_row:
			return None
		return refresh_token_row[0]

	async def delete_by_user_auth_id(self, user_auth_id: int) -> bool:
		return await self._delete(RefreshToken.user_auth_id, user_auth_id)

	async def delete(self, id: int) -> bool:
		return await self._delete(RefreshToken.id, id)

	async def _delete(self, field: Mapped, value: Any) -> bool:
		stmt = select(UserAuth).where(field == value)
		result = await self._async_session.execute(stmt)
		if not result:
			return False
		refresh_token_row = result.first()
		if not refresh_token_row:
			return False
		refresh_token = refresh_token_row[0]
		if not refresh_token:
			return False
		await self._async_session.delete(refresh_token)
		await self._async_session.flush()
		return True
