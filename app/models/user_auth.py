from .base import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Integer
from .timestamp_mixin import TimestampMixin
from typing import TYPE_CHECKING

if TYPE_CHECKING:
	from refresh_token import RefreshToken


class UserAuth(Base, TimestampMixin):
	__tablename__ = 'user_auth'

	id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False, autoincrement=True)
	email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
	hashed_password: Mapped[str] = mapped_column(String, nullable=False)

	refresh_token: Mapped['RefreshToken'] = relationship(back_populates='user_auth')
