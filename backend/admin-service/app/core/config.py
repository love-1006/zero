from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Must match login-service's JWT_SECRET — this service only verifies
    # tokens issued by login-service, it never issues its own (it does
    # re-sign refreshed tokens with the same secret, see core/security.py).
    jwt_secret: str = "dev-secret-change-me"
    # Must match login-service's JWT_EXPIRE_MINUTES — used when reissuing a
    # refreshed token so the sliding-session lifetime is consistent everywhere.
    jwt_expire_minutes: int = 180

    frontend_url: str = "http://localhost:3000"


settings = Settings()
