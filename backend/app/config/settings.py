from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Stock Filter API"
    debug: bool = False
    api_prefix: str = "/api/v1"

    class Config:
        env_file = ".env"


settings = Settings()
