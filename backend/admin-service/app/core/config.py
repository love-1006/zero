from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Must match login-service's JWT_SECRET — this service only verifies
    # tokens issued by login-service, it never issues its own.
    jwt_secret: str = "dev-secret-change-me"

    frontend_url: str = "http://localhost:3000"


settings = Settings()
