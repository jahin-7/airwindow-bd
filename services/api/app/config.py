"""Runtime settings from environment variables (see .env.example)."""
from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[3]
# The API reuses the training package so live features match training exactly.
sys.path.insert(0, str(ROOT / "ml" / "src"))

DHAKA_TZ = ZoneInfo("Asia/Dhaka")


def _load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())


_load_dotenv(ROOT / "services" / "api" / ".env")


@dataclass
class Settings:
    openaq_api_key: str = field(default_factory=lambda: os.getenv("OPENAQ_API_KEY", ""))
    data_dir: Path = field(default_factory=lambda: Path(os.getenv("AIRWINDOW_DATA_DIR", ROOT / "data" / "kaggle_upload")))
    artifacts_dir: Path = field(default_factory=lambda: Path(os.getenv("AIRWINDOW_ARTIFACTS", ROOT / "ml" / "artifacts")))
    stale_after_h: int = field(default_factory=lambda: int(os.getenv("STALE_AFTER_HOURS", "3")))
    cors_origins: list = field(default_factory=lambda: os.getenv("CORS_ORIGINS", "http://localhost:3010").split(","))
    rate_limit_per_min: int = field(default_factory=lambda: int(os.getenv("RATE_LIMIT_PER_MIN", "120")))


settings = Settings()
