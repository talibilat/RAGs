"""Simple configuration management using Pydantic Settings."""
import logging
from pydantic import Field
from pydantic_settings import BaseSettings
from typing import Optional

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """Application settings loaded from .env file."""
    
    # Database Configuration
    database_hostname: str = Field(default="localhost", env="DATABASE_HOSTNAME")
    database_port: str = Field(default="5432", env="DATABASE_PORT")
    database_name: str = Field(default="9fin", env="DATABASE_NAME")
    database_username: str = Field(default="postgres", env="DATABASE_USERNAME")
    database_password: str = Field(default="password", env="DATABASE_PASSWORD")
    
    # OpenAI Configuration
    openai_api_key: str = Field(env="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4o-mini", env="OPENAI_MODEL")
    
    # Application Configuration
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    data_path: str = Field(default="financial_data.json", env="DATA_PATH")
    agent_offline_mode: bool = Field(default=False, env="AGENT_OFFLINE_MODE")
    feature_agent_enabled: bool = Field(default=False, env="FEATURE_AGENT_ENABLED")
    
    # Performance Configuration
    db_max_connections: int = Field(default=20, env="DB_MAX_CONNECTIONS")
    db_connection_timeout: int = Field(default=30, env="DB_CONNECTION_TIMEOUT")
    query_timeout: int = Field(default=60, env="QUERY_TIMEOUT")
    
    @property
    def database_url(self) -> str:
        """Build database URL from configuration."""
        return (
            f"postgresql+psycopg2://{self.database_username}:{self.database_password}"
            f"@{self.database_hostname}:{self.database_port}/{self.database_name}"
        )
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()


def validate_config() -> None:
    """Validate required configuration."""
    if not settings.openai_api_key:
        raise RuntimeError("Missing required configuration: OPENAI_API_KEY")
    
    logger.info("Configuration validated successfully")
