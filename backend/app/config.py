"""Application configuration using Pydantic Settings.

All environment variables are loaded and validated here.
No other module should call os.getenv directly.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings, loaded from environment variables."""

    # Core
    log_level: str = "INFO"
    tz: str = "America/New_York"

    # Firestore
    gcp_project_id: str = "wolfiero-dev"
    google_application_credentials: str = ""
    firestore_emulator_host: str = ""

    # Market Data
    market_data_provider: str = "yahoo"
    market_data_api_key: str = ""
    market_data_api_secret: str = ""

    # News
    news_provider: str = ""
    news_api_key: str = ""

    # AI
    ai_provider: str = "anthropic"
    ai_api_key: str = ""
    ai_model: str = "claude-opus-5"

    # Telegram
    telegram_bot_token: str = ""
    telegram_allowed_chat_ids: str = ""

    # Strategy
    strategy_version: str = "v1.0.0"
    universe_min_dollar_volume: int = 20_000_000
    universe_min_price: float = 5.00
    scan_max_candidates: int = 20
    min_reward_risk: float = 2.0
    min_setup_quality: float = 0.45
    account_equity_usd: float = 100_000
    risk_per_trade_pct: float = 1.0
    max_portfolio_heat_pct: float = 6.0
    max_positions: int = 8
    max_sector_exposure_pct: float = 30.0
    hold_window_days: int = 15
    earnings_policy: str = "veto"

    # Scheduling
    premarket_run_time: str = "05:30"
    report_send_time: str = "07:00"
    intraday_interval_minutes: int = 5
    eod_report_time: str = "16:30"

    # Data Quality
    min_data_coverage_pct: float = 90.0
    max_data_staleness_days: int = 3
    max_daily_move_pct: float = 50.0

    # Monitoring
    watchdog_check_time: str = "07:15"
    grounding_guard_mode: str = "log"

    class Config:
        """Pydantic config."""

        env_file = ".env"
        case_sensitive = False

    def validate_strategy_weights(self) -> None:
        """Placeholder for strategy weight validation.

        Will load YAML and assert weights sum to 1.0.
        """

    def __post_init__(self) -> None:
        """Post-init validation."""
        # Validate risk percentages
        if not 0 < self.risk_per_trade_pct < 5:
            raise ValueError("risk_per_trade_pct must be between 0 and 5")

        # Validate portfolio heat
        if not 0 < self.max_portfolio_heat_pct <= 50:
            raise ValueError("max_portfolio_heat_pct must be between 0 and 50")

        # Validate R:R floor
        if self.min_reward_risk < 1.0:
            raise ValueError("min_reward_risk must be >= 1.0")

        # Validate setup quality
        if not 0 <= self.min_setup_quality <= 1:
            raise ValueError("min_setup_quality must be between 0 and 1")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Get cached settings singleton."""
    return Settings()
