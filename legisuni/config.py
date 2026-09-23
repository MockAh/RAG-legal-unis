from pathlib import Path

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuración global de LegisUni, cargada desde variables de entorno o `.env`."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="LEGISUNI_",
        extra="ignore",
    )

    anthropic_api_key: SecretStr | None = None
    modelo_llm: str = ""
    user_agent: str
    data_root: Path = Path("data")
    db_path: Path = Path("legisuni_v2.db")
    timeout_s: int = 30
    max_bytes: int = 100 * 1024 * 1024
    rate_limit_s: float = 1.0
    max_reintentos: int = 5
    paralelismo_dominios: int = 4

    def __repr__(self) -> str:
        # SecretStr ya se enmascara en su propio repr, evitando fugas en tracebacks
        fields = ", ".join(f"{name}={value!r}" for name, value in self)
        return f"{self.__class__.__name__}({fields})"
