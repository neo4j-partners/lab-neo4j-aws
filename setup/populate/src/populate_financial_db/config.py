"""
Configuration for the populate-financial-db CLI.

Loads settings from environment variables with fallback to CONFIG.txt
at the repository root.
"""

from pathlib import Path

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Resolve CONFIG.txt at repo root (setup/populate/../../CONFIG.txt)
_config_file = Path(__file__).resolve().parents[4] / "CONFIG.txt"
load_dotenv(_config_file)

# Also load .env if it exists (local override)
_env_file = Path(__file__).resolve().parents[4] / ".env"
if _env_file.exists():
    load_dotenv(_env_file, override=True)


class Settings(BaseSettings):
    """Settings loaded from environment / CONFIG.txt."""

    model_config = SettingsConfigDict(env_prefix="", extra="ignore")

    neo4j_uri: str = Field(validation_alias="NEO4J_URI")
    neo4j_username: str = Field(default="neo4j", validation_alias="NEO4J_USERNAME")
    neo4j_password: str = Field(validation_alias="NEO4J_PASSWORD")
    data_dir: str = Field(default="TransformedData/", validation_alias="DATA_DIR")

    @property
    def resolved_data_dir(self) -> Path:
        """Return data_dir as an absolute path, resolved relative to the repo root."""
        p = Path(self.data_dir)
        if p.is_absolute():
            return p
        return Path(__file__).resolve().parents[4] / p
