from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import PostgresDsn, computed_field
from pydantic_core import MultiHostUrl


class Settings(BaseSettings):
	model_config = SettingsConfigDict(
		env_file=".env",
		env_ignore_empty=True,
		extra="ignore",
	)

	JWT_ALGORITHM: str
	JWT_SECRET_KEY: str
	ACCESS_TOKEN_EXPIRE_MINUTES: int

	POSTGRES_SERVER: str
	POSTGRES_PORT: int
	POSTGRES_USER: str
	POSTGRES_PASSWORD: str
	POSTGRES_DB: str

	@computed_field
	@property
	def POSTGRES_URL(self) -> PostgresDsn | MultiHostUrl:
		return MultiHostUrl.build(
			scheme="postgresql",
			username=self.POSTGRES_USER,
			password=self.POSTGRES_PASSWORD,
			host=self.POSTGRES_SERVER,
			port=self.POSTGRES_PORT,
			path=self.POSTGRES_DB,
		)

	@computed_field
	@property
	def POSTGRES_URL_ASYNC(self) -> PostgresDsn | MultiHostUrl:
		return MultiHostUrl.build(
			scheme="postgresql+asyncpg",
			username=self.POSTGRES_USER,
			password=self.POSTGRES_PASSWORD,
			host=self.POSTGRES_SERVER,
			port=self.POSTGRES_PORT,
			path=self.POSTGRES_DB,
		)


settings = Settings()
