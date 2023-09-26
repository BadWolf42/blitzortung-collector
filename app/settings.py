from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    debug: bool = False
    postgres_user: str  = 'pguser'
    postgres_password: str  = 'pgsecret'
    postgres_host: str  = 'db'
    postgres_port: str  = '5432'
    postgres_database: str  = 'blitzdb'

settings = Settings()
