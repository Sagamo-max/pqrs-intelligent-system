from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "Ticket Intelligent Triage API"
    API_V1_STR: str = "/api/v1"

    DATABASE_URL: str
    
    AI_PROVIDER: str = "openai"
    OPENAI_API_KEY: str
    AI_MODEL_NAME: str
    AI_BASE_URL: str | None = None
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    JWT_REFRESH_SECRET_KEY: str
    JWT_REFRESH_EXPIRE_DAYS: int = 7

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()