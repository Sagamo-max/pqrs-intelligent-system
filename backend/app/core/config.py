from pydantic import computed_field
from pydantic_core import MultiHostUrl
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "Ticket Intelligent Triage API"
    API_V1_STR: str = "/api/v1"
    
    POSTGRES_PASSWORD: str
    
    AI_PROVIDER: str = "openai"
    AI_API_KEY: str
    AI_MODEL_NAME: str

    @computed_field
    @property
    def DATABASE_URL(self) -> str:
        return str(
            MultiHostUrl.build(
                scheme="postgresql",
                username="postgres",
                password=self.POSTGRES_PASSWORD,
                host="localhost",
                port=5432,
                path="ticket_db",
            )
        )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()