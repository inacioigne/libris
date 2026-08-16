from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str
    elasticsearch_url: str = "http://elastic:9200"
    secret_key: str

    class Config:
        env_file = ".env"


settings = Settings()