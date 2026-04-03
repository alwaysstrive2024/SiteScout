"""
SiteScout (灵嗅) – Entry point
Run with:  python main.py
Or:        uvicorn app.main:app --reload
"""

import uvicorn
from app.config import get_settings


def main() -> None:
    cfg = get_settings()
    uvicorn.run(
        "app.main:app",
        host=cfg.host,
        port=cfg.port,
        log_level=cfg.log_level,
        reload=True,   # flip to False in production
    )


if __name__ == "__main__":
    main()
