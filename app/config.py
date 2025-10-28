from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    mongo_uri: str
    mongodb_db: str
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    openai_api_key: str

    class Config:
        env_file = ".env"
        extra ="allow"

settings = Settings()
