from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    database_url: str = "sqlite:///./smartstok.db"
    jwt_secret: str = "smartstok-secret-change-me"
    cors_origins: str = "http://localhost:5173"
    llm_api_url: str = ""
    llm_api_key: str = ""
    llm_model: str = ""
    model_config = SettingsConfigDict(env_file="../.env", extra="ignore")

settings = Settings()
