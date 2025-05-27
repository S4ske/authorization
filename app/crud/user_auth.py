from sqlalchemy.ext.asyncio import AsyncSession
from ..models import UserAuth
from sqlalchemy import select
from sqlalchemy.orm import Mapped
from typing import Any
from ..schemas import UserAuthUpdateSchema


class UserAuthRepository:
	def __init__(self, async_session: AsyncSession):
		self._async_session = async_session

	async def create(self, email: str, hashed_password: str) -> UserAuth:
		user_auth = UserAuth(email=email, hashed_password=hashed_password)
		self._async_session.add(user_auth)
		await self._async_session.flush()
		await self._async_session.refresh(user_auth)
		return user_auth

	async def get_by_email(self, email: str) -> UserAuth | None:
		return await self._get(UserAuth.email, email)

	async def get_by_id(self, id: int) -> UserAuth | None:
		return await self._get(UserAuth.id, id)

	async def _get(self, field: Mapped, value: Any) -> UserAuth | None:
		stmt = select(UserAuth).where(field == value)
		result = await self._async_session.execute(stmt)
		if not result:
			return None
		user_auth = result.first()
		if not user_auth:
			return None
		return user_auth[0]

	async def update(self, id: int, user_auth_update_schema: UserAuthUpdateSchema) -> UserAuth | None:
		user_auth = await self.get_by_id(id)
		if not user_auth:
			return None

		for field, value in user_auth_update_schema.model_dump(exclude_unset=True).items():
			setattr(user_auth, field, value)

		await self._async_session.flush()
		await self._async_session.refresh(user_auth)
		return user_auth

	async def delete(self, email: str) -> bool:
		user_auth = await self.get_by_email(email)
		if not user_auth:
			return False

		await self._async_session.delete(user_auth)
		await self._async_session.flush()
		return True
