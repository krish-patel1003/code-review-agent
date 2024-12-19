from pydantic import BaseSettings


class Settings(BaseSettings):

    database_url = str

    class Config:
        env_file = "..env.dev"

settings = Settings()