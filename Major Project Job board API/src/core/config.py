from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv 

load_dotenv()

# Configuration settings loaded from the environment/.env file.
class Settings(BaseSettings):
    
    APP_NAME: str = "Job Board API"
    ENV_STATE: str = "development"
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8')

    DATABASE_HOSTNAME: str
    DATABASE_PORT: int
    DATABASE_PASSWORD: str
    DATABASE_NAME: str
    DATABASE_USERNAME: str
    
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int

settings = Settings()

BYPASS_MIDDLEWARE_PATHS = [
    r"^/$",
    r"^/users/login/?$", r"^/users/register/?$",
    r"^/companies/?$", r"^/companies/\d+/?$",
    r"^/listings/?$", r"^/listings/\d+/?$",
    r"^/seekers/?$", r"^/seekers/\d+/?$",
    r"^/recruiters/?$", r"^/recruiters/\d+/?$",
]