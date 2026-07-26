from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str

    elasticsearch_url: str = "http://elasticsearch:9200"

    class Config:
        env_file = ".env"


settings = Settings()