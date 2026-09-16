from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - convenience before installing requirements
    load_dotenv = None


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
REPORTS_DIR = PROJECT_ROOT / "reports"
DB_PATH = DATA_DIR / "sidepick.db"


@dataclass(frozen=True)
class CategoryConfig:
    key: str
    name: str
    category_id: str
    seeds: tuple[str, ...]


@dataclass(frozen=True)
class Settings:
    naver_client_id: str
    naver_client_secret: str
    categories: tuple[CategoryConfig, ...]
    seed_display: int = 50
    candidate_display: int = 50
    min_keyword_frequency: int = 2
    max_candidates_per_category: int = 25
    trend_weeks: int = 8


def load_settings() -> Settings:
    env_path = PROJECT_ROOT / ".env"
    if load_dotenv:
        load_dotenv(env_path)
    else:
        _load_dotenv_fallback(env_path)

    categories = (
        CategoryConfig(
            key="auto",
            name="자동차용품",
            category_id=os.getenv("SIDEPICK_CATEGORY_ID_AUTO", "").strip(),
            seeds=("차량용품", "차량용 수납", "차량용 청소", "차박 용품", "자동차 인테리어"),
        ),
        CategoryConfig(
            key="living",
            name="생활용품",
            category_id=os.getenv("SIDEPICK_CATEGORY_ID_LIVING", "").strip(),
            seeds=("생활용품", "욕실용품", "주방 정리", "청소용품", "수납용품"),
        ),
        CategoryConfig(
            key="camping",
            name="캠핑용품",
            category_id=os.getenv("SIDEPICK_CATEGORY_ID_CAMPING", "").strip(),
            seeds=("캠핑용품", "캠핑 수납", "캠핑 조명", "차박 캠핑", "캠핑 주방용품"),
        ),
    )

    return Settings(
        naver_client_id=os.getenv("NAVER_CLIENT_ID", "").strip(),
        naver_client_secret=os.getenv("NAVER_CLIENT_SECRET", "").strip(),
        categories=categories,
    )


def require_naver_credentials(settings: Settings) -> None:
    missing = []
    if not settings.naver_client_id:
        missing.append("NAVER_CLIENT_ID")
    if not settings.naver_client_secret:
        missing.append("NAVER_CLIENT_SECRET")
    if missing:
        joined = ", ".join(missing)
        raise RuntimeError(f"Missing required Naver API credentials in .env: {joined}")


def _load_dotenv_fallback(path: Path) -> None:
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))
