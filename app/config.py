from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    DATABASE_URL: str

    POSTGRES_USER: str = "opc_user"
    POSTGRES_PASSWORD: str = "opc_password"
    POSTGRES_DB: str = "opc_db"
    POSTGRES_HOST: str = "db"
    POSTGRES_PORT: int = 5432

    JWT_SECRET: str = "change-me-in-production-use-a-long-random-string"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7


settings = Settings()  # type: ignore[call-arg]
