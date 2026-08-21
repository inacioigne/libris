from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str
    elasticsearch_url: str = "http://elastic:9200"
    secret_key: str
    admin_username: str | None = None
    admin_password: str | None = None
    admin_email: str | None = None

    class Config:
        env_file = ".env"


settings = Settings()