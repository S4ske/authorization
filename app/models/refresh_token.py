from .base import Base
from .timestamp_mixin import TimestampMixin
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, DateTime, Integer, ForeignKey
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
	from user_auth import UserAuth


class RefreshToken(Base, TimestampMixin):
	__tablename__ = 'refresh_tokens'

	id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False, autoincrement=True)
	hashed_token: Mapped[str] = mapped_column(String, nullable=False)
	expires_at: Mapped[datetime] = mapped_column(DateTime)
	user_auth_id: Mapped[int] = mapped_column(ForeignKey('user_auth.id'), unique=True)

	user_auth: Mapped['UserAuth'] = relationship(back_populates='refresh_token')
