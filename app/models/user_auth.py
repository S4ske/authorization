from .base import Base
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String


class UserAuth(Base):
	__tablename__ = 'user_auth'

	id: Mapped[int] = mapped_column(primary_key=True, nullable=False, autoincrement=True)
	email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
	hashed_password: Mapped[str] = mapped_column(String, nullable=False)
