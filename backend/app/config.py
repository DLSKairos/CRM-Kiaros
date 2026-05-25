from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str
    database_url_sync: str
    redis_url: str = "redis://localhost:6379/0"

    # Proveedor de IA: "anthropic" (pago) o "groq" (gratuito)
    ai_provider: str = "anthropic"

    # Anthropic
    anthropic_api_key: str = ""

    # Groq (gratuito — api.groq.com)
    groq_api_key: str = ""

    # Notificaciones
    resend_api_key: str = ""
    resend_to_email: str = ""
    slack_webhook_url: str = ""
    output_dir: str = "/output"


settings = Settings()
