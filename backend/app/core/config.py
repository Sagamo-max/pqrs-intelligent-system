from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "PQRS Intelligent Triage API"
    API_V1_STR: str = "/api/v1"
    
    # Cadena de conexión a PostgreSQL
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/pqrs_db"
    
    # Proveedores de IA (Gemini / Groq)
    AI_PROVIDER: str = "gemini"
    AI_API_KEY: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()