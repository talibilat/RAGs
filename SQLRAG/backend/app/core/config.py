"""Simple configuration management using Pydantic Settings."""
import logging
from typing import Optional, Any, Literal
from pydantic import Field
from pydantic_settings import BaseSettings

logger = logging.getLogger(__name__)


def _normalize_url_for_driver(url: str, driver: Literal["sync", "async"]) -> str:
    """
    Normalize a SQLAlchemy URL to the correct driver family.
    Helps when DATABASE_URL is provided with the wrong (async/sync) driver.
    """
    if driver == "sync":
        url = url.replace("+asyncpg", "+psycopg2")
        url = url.replace("sqlite+aiosqlite://", "sqlite://")
    else:
        # async
        url = url.replace("+psycopg2", "+asyncpg")
        # handle bare postgres urls
        if "postgresql://" in url and "+asyncpg" not in url and "+psycopg2" not in url:
            url = url.replace("postgresql://", "postgresql+asyncpg://")
        if "sqlite://" in url and "+aiosqlite" not in url:
            url = url.replace("sqlite://", "sqlite+aiosqlite://")
    return url


class Settings(BaseSettings):
    """Application settings loaded from .env file."""
    
    # Security / Auth
    secret_key: str = Field(default="change-me", env="SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", env="JWT_ALGORITHM")
    access_token_exp_minutes: int = Field(default=60 * 24, env="ACCESS_TOKEN_EXP_MINUTES")
    
    # Database Configuration
    database_url_override: Optional[str] = Field(default=None, env="DATABASE_URL")
    database_hostname: str = Field(default="localhost", env="DATABASE_HOSTNAME")
    database_port: str = Field(default="5432", env="DATABASE_PORT")
    # Default to SQLite to avoid requiring external DB services.
    database_name: str = Field(default="sqlrag.db", env="DATABASE_NAME")
    database_username: str = Field(default="sqlite", env="DATABASE_USERNAME")
    database_password: str = Field(default="password", env="DATABASE_PASSWORD")
    
    # Azure OpenAI Configuration
    azure_openai_endpoint: Optional[str] = Field(default=None, env="AZURE_OPENAI_ENDPOINT")
    azure_openai_api_key: Optional[str] = Field(default=None, env="AZURE_OPENAI_API_KEY")
    azure_openai_deployment: str = Field(default="gpt-5-chat", env="AZURE_OPENAI_DEPLOYMENT")
    azure_openai_api_version: str = Field(default="2025-01-01-preview", env="AZURE_OPENAI_API_VERSION")
    
    # Generic OpenAI Configuration (to avoid validation errors if set in environment)
    openai_api_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    openai_model: Optional[str] = Field(default="gpt-4o", env="OPENAI_MODEL")
    
    # Application Configuration
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    data_path: str = Field(default="financial_data.json", env="DATA_PATH")
    agent_offline_mode: bool = Field(default=False, env="AGENT_OFFLINE_MODE")
    feature_agent_enabled: bool = Field(default=False, env="FEATURE_AGENT_ENABLED")
    
    # Performance Configuration
    db_max_connections: int = Field(default=20, env="DB_MAX_CONNECTIONS")
    db_connection_timeout: int = Field(default=30, env="DB_CONNECTION_TIMEOUT")
    query_timeout: int = Field(default=60, env="QUERY_TIMEOUT")

    # Dev ergonomics
    # In production, DB is always treated as required regardless of this value.
    db_required: bool = Field(default=False, env="DB_REQUIRED")
    
    # Production Configuration
    environment: str = Field(default="development", env="ENVIRONMENT")
    allowed_origins: str = Field(default="http://localhost:3000,http://localhost:5173", env="ALLOWED_ORIGINS")
    enable_debug: bool = Field(default=False, env="ENABLE_DEBUG")
    checkpoint_path: str = Field(default="checkpoints/langgraph.db", env="CHECKPOINT_PATH")
    seed_demo_data: bool = Field(default=True, env="SEED_DEMO_DATA")
    
    @property
    def allowed_origins_list(self) -> list[str]:
        """Parse allowed origins from comma-separated string."""
        if self.allowed_origins == "*":
            return ["*"]
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]
    
    @property
    def database_url(self) -> str:
        """Build sync database URL from configuration."""
        if self.database_url_override:
            return _normalize_url_for_driver(self.database_url_override, "sync")
        # Check if using sqlite
        if self.database_username == "sqlite":
             return f"sqlite:///{self.database_name}"
        return (
            f"postgresql+psycopg2://{self.database_username}:{self.database_password}"
            f"@{self.database_hostname}:{self.database_port}/{self.database_name}"
        )

    @property
    def database_url_async(self) -> str:
        """Build async database URL for FastAPI/AsyncSQLAlchemy."""
        if self.database_url_override:
            return _normalize_url_for_driver(self.database_url_override, "async")
        if self.database_username == "sqlite":
             return f"sqlite+aiosqlite:///{self.database_name}"
        return (
            f"postgresql+asyncpg://{self.database_username}:{self.database_password}"
            f"@{self.database_hostname}:{self.database_port}/{self.database_name}"
        )

    @property
    def database_is_sqlite(self) -> bool:
        """Detect SQLite from the effective async database URL."""
        return self.database_url_async.lower().startswith("sqlite")

    @property
    def db_required_effective(self) -> bool:
        """Whether DB connectivity is required for startup/readiness."""
        return True if self.environment == "production" else bool(self.db_required)
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore"
    }

    @classmethod
    def _check_empty_to_default(cls, v, info):
        if v == "":
            return None # let default handle it? No, default needs field info.
            # actually if we return None and the field is not Optional, it might fail if default is not handled for None.
            # But BaseSettings might not use default if key exists.
            # Better strategy: return the default if v is empty string.
            return info.default
        return v
    
    # We can use validator or model_validator.
    # Pydantic V2 allows BeforeValidator.
    # Helper for int parsing
    @staticmethod
    def _parse_int(v: Any) -> Any:
        if v == "":
            return None
        return v
    
    # helper for bool parsing
    @staticmethod
    def _parse_bool(v: Any) -> Any:
        if v == "":
            return None
        return v

    # Actually, simpler approach for this specific issue:
    # Just make them Optional with defaults, or use a validator that ignores empty strings.
    # Let's use `model_validator(mode='before')` to clean up the env dict.
    
    from pydantic import model_validator

    @model_validator(mode='before')
    @classmethod
    def clean_empty_strings(cls, data: Any) -> Any:
        if isinstance(data, dict):
            return {
                k: v for k, v in data.items() 
                if v != "" 
            }
        return data


# Global settings instance
settings = Settings()

def validate_config() -> None:
    """Validate required configuration."""
    missing = []
    if not settings.azure_openai_api_key:
        missing.append("AZURE_OPENAI_API_KEY")
    if not settings.azure_openai_endpoint:
        missing.append("AZURE_OPENAI_ENDPOINT")
    
    # Only enforce non-default secret key in production
    if settings.environment == "production" and settings.secret_key in ("", "change-me"):
        missing.append("SECRET_KEY")
        
    if missing:
        raise RuntimeError(f"Missing required configuration: {', '.join(missing)}")

    logger.info("Configuration validated successfully", extra={"extra_data": {"env": settings.environment}})
