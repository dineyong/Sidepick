from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


SCHEMA = """
CREATE TABLE IF NOT EXISTS runs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  started_at TEXT NOT NULL,
  finished_at TEXT,
  notes TEXT
);

CREATE TABLE IF NOT EXISTS seed_products (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  run_id INTEGER NOT NULL,
  collected_at TEXT NOT NULL,
  source_category TEXT NOT NULL,
  seed_keyword TEXT NOT NULL,
  product_id TEXT,
  title TEXT NOT NULL,
  lprice INTEGER,
  hprice INTEGER,
  mall_name TEXT,
  brand TEXT,
  maker TEXT,
  category1 TEXT,
  category2 TEXT,
  category3 TEXT,
  category4 TEXT,
  raw_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS candidate_snapshots (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  run_id INTEGER NOT NULL,
  collected_at TEXT NOT NULL,
  source_category TEXT NOT NULL,
  candidate_keyword TEXT NOT NULL,
  extraction_frequency INTEGER NOT NULL,
  source_titles INTEGER NOT NULL,
  total_results INTEGER,
  avg_price REAL,
  median_price REAL,
  min_price INTEGER,
  max_price INTEGER,
  brand_count INTEGER,
  category_path TEXT,
  latest_trend_ratio REAL,
  trend_change_pct REAL,
  trend_points INTEGER,
  sidepick_score REAL,
  reason TEXT
);

CREATE TABLE IF NOT EXISTS candidate_products (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  run_id INTEGER NOT NULL,
  candidate_keyword TEXT NOT NULL,
  product_id TEXT,
  title TEXT NOT NULL,
  lprice INTEGER,
  hprice INTEGER,
  mall_name TEXT,
  brand TEXT,
  maker TEXT,
  category1 TEXT,
  category2 TEXT,
  category3 TEXT,
  category4 TEXT,
  raw_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS trend_points (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  run_id INTEGER NOT NULL,
  source_category TEXT NOT NULL,
  candidate_keyword TEXT NOT NULL,
  period TEXT NOT NULL,
  ratio REAL NOT NULL
);
"""


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class SidePickDb:
    def __init__(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(path)
        self.connection.row_factory = sqlite3.Row
        self.connection.executescript(SCHEMA)
        self.connection.commit()

    def start_run(self) -> int:
        cursor = self.connection.execute(
            "INSERT INTO runs (started_at, notes) VALUES (?, ?)",
            (utc_now(), "sidepick discover"),
        )
        self.connection.commit()
        return int(cursor.lastrowid)

    def finish_run(self, run_id: int) -> None:
        self.connection.execute(
            "UPDATE runs SET finished_at = ? WHERE id = ?",
            (utc_now(), run_id),
        )
        self.connection.commit()

    def insert_seed_products(
        self,
        run_id: int,
        source_category: str,
        seed_keyword: str,
        items: Iterable[dict],
    ) -> None:
        rows = [
            self._product_row(run_id, source_category, seed_keyword, item)
            for item in items
        ]
        self.connection.executemany(
            """
            INSERT INTO seed_products (
              run_id, collected_at, source_category, seed_keyword, product_id, title,
              lprice, hprice, mall_name, brand, maker, category1, category2,
              category3, category4, raw_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            rows,
        )
        self.connection.commit()

    def insert_candidate_products(
        self,
        run_id: int,
        candidate_keyword: str,
        items: Iterable[dict],
    ) -> None:
        rows = []
        for item in items:
            row = self._product_row(run_id, "", candidate_keyword, item)
            rows.append(
                (
                    row[0],
                    row[3],
                    row[4],
                    row[5],
                    row[6],
                    row[7],
                    row[8],
                    row[9],
                    row[10],
                    row[11],
                    row[12],
                    row[13],
                    row[14],
                    row[15],
                )
            )
        self.connection.executemany(
            """
            INSERT INTO candidate_products (
              run_id, candidate_keyword, product_id, title,
              lprice, hprice, mall_name, brand, maker, category1, category2,
              category3, category4, raw_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            rows,
        )
        self.connection.commit()

    def insert_trend_points(
        self,
        run_id: int,
        source_category: str,
        candidate_keyword: str,
        data: Iterable[dict],
    ) -> None:
        rows = [
            (
                run_id,
                source_category,
                candidate_keyword,
                point["period"],
                float(point["ratio"]),
            )
            for point in data
        ]
        self.connection.executemany(
            """
            INSERT INTO trend_points (
              run_id, source_category, candidate_keyword, period, ratio
            ) VALUES (?, ?, ?, ?, ?)
            """,
            rows,
        )
        self.connection.commit()

    def insert_candidate_snapshot(self, run_id: int, row: dict) -> None:
        self.connection.execute(
            """
            INSERT INTO candidate_snapshots (
              run_id, collected_at, source_category, candidate_keyword,
              extraction_frequency, source_titles, total_results, avg_price,
              median_price, min_price, max_price, brand_count, category_path,
              latest_trend_ratio, trend_change_pct, trend_points, sidepick_score,
              reason
            ) VALUES (
              :run_id, :collected_at, :source_category, :candidate_keyword,
              :extraction_frequency, :source_titles, :total_results, :avg_price,
              :median_price, :min_price, :max_price, :brand_count, :category_path,
              :latest_trend_ratio, :trend_change_pct, :trend_points, :sidepick_score,
              :reason
            )
            """,
            {"run_id": run_id, "collected_at": utc_now(), **row},
        )
        self.connection.commit()

    def _product_row(
        self,
        run_id: int,
        source_category: str,
        seed_keyword: str,
        item: dict,
    ) -> tuple:
        return (
            run_id,
            utc_now(),
            source_category,
            seed_keyword,
            str(item.get("productId", "")),
            item.get("title", ""),
            _to_int(item.get("lprice")),
            _to_int(item.get("hprice")),
            item.get("mallName", ""),
            item.get("brand", ""),
            item.get("maker", ""),
            item.get("category1", ""),
            item.get("category2", ""),
            item.get("category3", ""),
            item.get("category4", ""),
            json.dumps(item, ensure_ascii=False),
        )


def _to_int(value: object) -> int | None:
    try:
        parsed = int(str(value or "0"))
    except ValueError:
        return None
    return parsed if parsed > 0 else None
