from pydantic import BaseModel, EmailStr, Field


class UserAuthIn(BaseModel):
	email: EmailStr = Field(max_length=255)
	password: str = Field(max_length=30)


class UserAuthUpdate(BaseModel):
	email: EmailStr | None = Field(max_length=255, default=None)
	hashed_password: str | None = None
