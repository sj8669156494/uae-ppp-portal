from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_env: str = "development"
    log_level: str = "INFO"
    secret_key: str = "change-this"

    database_url: str = "sqlite+aiosqlite:///./uae_ppp.db"

    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"

    frontend_url: str = "http://localhost:5173"

    scraper_delay_seconds: int = 2
    scraper_timeout_seconds: int = 30
    max_retries: int = 3
    scraper_user_agent: str = "Mozilla/5.0 (compatible; UAE-PPP-Bot/1.0; research)"

    scraper_schedule_hour: int = 6
    scraper_schedule_minute: int = 0

    enable_query_logging: bool = True
    log_file_path: str = "logs/uae_ppp.log"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


settings = Settings()
