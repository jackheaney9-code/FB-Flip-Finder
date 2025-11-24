from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # --- Facebook defaults ---
    FB_EMAIL: str | None = None
    FB_PASSWORD: str | None = None
    FB_COOKIE_PATH: str = "/tmp/fb_cookies.json"
    FB_KEYWORDS: list[str] = []
    FB_REGION_NAME: str | None = None
    FB_RADIUS_KM: int = 50
    FB_MAX_PAGES: int = 2

    # --- Deal thresholds ---
    MIN_PROFIT: float = 50.0
    MIN_ROI: float = 0.2
    EMAIL_ON_DEAL: bool = True

    # --- Gmail / SMTP ---
    SMTP_USER: str | None = None
    SMTP_PASS: str | None = None
    DEAL_TO_EMAIL: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"  # ignore any unknown keys
    )

settings = Settings()
