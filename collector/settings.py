from pydantic_settings import BaseSettings, SettingsConfigDict


class CollectorSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Inherited from .env (same file used by the API)
    DATABASE_URL: str

    # Injected by docker-compose for the collector service
    OPCUA_URL: str = "opc.tcp://simulator:4840"

    # How often (in seconds) the collector polls the OPC-UA server
    POLL_INTERVAL: float = 5.0

    # Exponential backoff settings for OPC-UA reconnection
    RETRY_BASE_DELAY: float = 1.0   # first retry waits 1 s
    RETRY_MAX_DELAY: float = 60.0   # cap at 60 s


settings = CollectorSettings()  # type: ignore[call-arg]
