from __future__ import annotations

import json
from html import escape
from pathlib import Path


def print_top_results(rows: list[dict], top: int) -> None:
    print(f"\nSidePick TOP {min(top, len(rows))}\n")
    for rank, row in enumerate(rows[:top], start=1):
        trend = row["trend_change_pct"]
        trend_text = "N/A" if trend is None else f"{trend:+.1f}%"
        avg_price = _money(row["avg_price"])
        median_price = _money(row["median_price"])
        print(
            f"{rank:02d}. {row['candidate_keyword']} | "
            f"Score {row['sidepick_score']:.2f} | "
            f"Trend {trend_text} | "
            f"Competition {row['total_results']:,} | "
            f"Avg {avg_price} / Median {median_price}"
        )
        print(f"    Reason: {row['reason']}")


def write_reports(rows: list[dict], report_dir: Path, top: int) -> tuple[Path, Path]:
    report_dir.mkdir(parents=True, exist_ok=True)
    json_path = report_dir / "latest.json"
    html_path = report_dir / "latest.html"
    selected = rows[:top]
    json_path.write_text(json.dumps(selected, ensure_ascii=False, indent=2), encoding="utf-8")
    html_path.write_text(_render_html(selected), encoding="utf-8")
    return json_path, html_path


def _render_html(rows: list[dict]) -> str:
    table_rows = []
    for index, row in enumerate(rows, start=1):
        trend = row["trend_change_pct"]
        trend_text = "N/A" if trend is None else f"{trend:+.1f}%"
        table_rows.append(
            "<tr>"
            f"<td>{index}</td>"
            f"<td>{escape(row['candidate_keyword'])}</td>"
            f"<td>{row['sidepick_score']:.2f}</td>"
            f"<td>{trend_text}</td>"
            f"<td>{row['total_results']:,}</td>"
            f"<td>{_money(row['avg_price'])}</td>"
            f"<td>{_money(row['median_price'])}</td>"
            f"<td>{escape(row['reason'])}</td>"
            "</tr>"
        )
    return f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>SidePick TOP Candidates</title>
  <style>
    body {{ font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; margin: 32px; color: #202124; }}
    h1 {{ margin-bottom: 4px; }}
    p {{ color: #5f6368; }}
    table {{ border-collapse: collapse; width: 100%; margin-top: 24px; }}
    th, td {{ border-bottom: 1px solid #e8eaed; padding: 10px 8px; text-align: left; vertical-align: top; }}
    th {{ background: #f8f9fa; font-size: 13px; }}
    td:nth-child(3), td:nth-child(4), td:nth-child(5), td:nth-child(6), td:nth-child(7) {{ white-space: nowrap; }}
  </style>
</head>
<body>
  <h1>SidePick TOP Candidates</h1>
  <p>Official Naver API data only. No sales, revenue, or exact search volume estimates.</p>
  <table>
    <thead>
      <tr>
        <th>#</th><th>상품 후보명</th><th>Score</th><th>최근 트렌드 변화</th>
        <th>경쟁상품 규모</th><th>평균 판매가격</th><th>중앙 판매가격</th><th>추천된 이유</th>
      </tr>
    </thead>
    <tbody>
      {''.join(table_rows)}
    </tbody>
  </table>
</body>
</html>
"""


def _money(value: float | int | None) -> str:
    if value is None:
        return "N/A"
    return f"{value:,.0f}원"

