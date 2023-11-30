from pydantic import SecretStr, PostgresDsn
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    bot_token: SecretStr
    db_url: PostgresDsn

    class Config:
        env_file = '.env'


config = Settings()