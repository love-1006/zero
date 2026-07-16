from urllib.parse import quote_plus

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Must match login-service's JWT_SECRET — this service only verifies
    # tokens issued by login-service, it never issues its own (it does
    # re-sign refreshed tokens with the same secret, see core/security.py).
    jwt_secret: str = "dev-secret-change-me"
    # Must match login-service's JWT_EXPIRE_MINUTES (sliding-session refresh).
    jwt_expire_minutes: int = 180

    frontend_url: str = "http://localhost:3000"

    # Same Postgres instance as login-service/main-service. Unlike the `service`
    # schema (data-team managed), this service owns and self-migrates its own
    # `community` schema — see app/core/database.py.
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "test_db"
    postgres_user: str = ""
    postgres_password: str = ""

    @property
    def database_url(self) -> str:
        user = quote_plus(self.postgres_user)
        password = quote_plus(self.postgres_password)
        return f"postgresql+asyncpg://{user}:{password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"


settings = Settings()
