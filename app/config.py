from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    ollama_base_url: str = "http://localhost:11434"
    llm_gateway_api_keys: str = "dev-key-change-me"
    rate_limit_requests: int = 20
    rate_limit_window_seconds: int = 60
    max_concurrency: int = 2
    queue_timeout_seconds: int = 60

    @property
    def api_keys(self) -> set[str]:
        return {k.strip() for k in self.llm_gateway_api_keys.split(",") if k.strip()}


settings = Settings()
