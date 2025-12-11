from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """
    Configuration settings loaded from the environment/.env file.
    """
    APP_NAME: str = "Recipe API"
    ENV_STATE: str = "development"
    
    DATABASE_URL: str

    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int

    model_config = SettingsConfigDict(
        env_file=".env", 
        extra="ignore"  
    )

settings = Settings()