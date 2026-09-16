from __future__ import annotations

from collections import defaultdict

from sidepick.config import REPORTS_DIR, Settings, require_naver_credentials
from sidepick.db import SidePickDb
from sidepick.keyword_extractor import clean_title, extract_keywords
from sidepick.naver import NaverApiError, NaverClient
from sidepick.report import print_top_results, write_reports
from sidepick.scoring import CandidateMetrics, score_candidates


def run_discovery(settings: Settings, db: SidePickDb, top: int = 20) -> list[dict]:
    require_naver_credentials(settings)
    client = NaverClient(settings.naver_client_id, settings.naver_client_secret)
    run_id = db.start_run()

    try:
        all_metrics: list[CandidateMetrics] = []
        for category in settings.categories:
            titles: list[str] = []
            print(f"\n[{category.name}] seed 상품 수집")
            for seed in category.seeds:
                response = client.search_shop(seed, display=settings.seed_display)
                items = response.get("items", [])
                db.insert_seed_products(run_id, category.name, seed, items)
                titles.extend(clean_title(item.get("title", "")) for item in items)
                print(f"  - {seed}: {len(items)} items, total={response.get('total', 0):,}")

            extracted = extract_keywords(
                titles,
                min_frequency=settings.min_keyword_frequency,
                limit=settings.max_candidates_per_category,
            )
            print(f"  후보 키워드 {len(extracted)}개 추출")

            trend_by_keyword = _fetch_trends(
                client=client,
                category_id=category.category_id,
                category_name=category.name,
                keywords=[item.keyword for item in extracted],
                weeks=settings.trend_weeks,
            )

            for keyword in extracted:
                response = client.search_shop(
                    keyword.keyword,
                    display=settings.candidate_display,
                )
                items = response.get("items", [])
                db.insert_candidate_products(run_id, keyword.keyword, items)

                trend = trend_by_keyword.get(keyword.keyword, [])
                if trend:
                    db.insert_trend_points(run_id, category.name, keyword.keyword, trend)

                metrics = _build_metrics(
                    keyword=keyword.keyword,
                    total_results=int(response.get("total", 0)),
                    extraction_frequency=keyword.frequency,
                    source_titles=keyword.source_titles,
                    items=items,
                    trend=trend,
                )
                all_metrics.append(metrics)

        scored = score_candidates(all_metrics)
        for row in scored:
            db.insert_candidate_snapshot(
                run_id,
                {
                    "source_category": _guess_source_category(row["category_path"]),
                    **row,
                    "sidepick_score": row["sidepick_score"],
                },
            )

        print_top_results(scored, top)
        json_path, html_path = write_reports(scored, REPORTS_DIR, top)
        print(f"\nSaved JSON report: {json_path}")
        print(f"Saved HTML report: {html_path}")
        return scored
    finally:
        db.finish_run(run_id)


def _fetch_trends(
    client: NaverClient,
    category_id: str,
    category_name: str,
    keywords: list[str],
    weeks: int,
) -> dict[str, list[dict]]:
    if not category_id:
        print(f"  DataLab skipped: {category_name} category_id is empty")
        return {}

    trend_by_keyword: dict[str, list[dict]] = {}
    for batch in _chunks(keywords, 5):
        try:
            response = client.shopping_keyword_trends(category_id, batch, weeks=weeks)
        except NaverApiError as error:
            print(f"  DataLab skipped for batch {batch}: {error}")
            continue
        for result in response.get("results", []):
            title = result.get("title", "")
            trend_by_keyword[title] = result.get("data", [])
    return trend_by_keyword


def _build_metrics(
    keyword: str,
    total_results: int,
    extraction_frequency: int,
    source_titles: int,
    items: list[dict],
    trend: list[dict],
) -> CandidateMetrics:
    prices = []
    brands = set()
    category_paths = []
    for item in items:
        try:
            price = int(str(item.get("lprice") or "0"))
        except ValueError:
            price = 0
        if price > 0:
            prices.append(price)
        brand = item.get("brand") or item.get("maker") or ""
        if brand:
            brands.add(brand)
        category_path = " > ".join(
            part
            for part in [
                item.get("category1", ""),
                item.get("category2", ""),
                item.get("category3", ""),
                item.get("category4", ""),
            ]
            if part
        )
        if category_path:
            category_paths.append(category_path)

    return CandidateMetrics(
        keyword=keyword,
        total_results=total_results,
        prices=prices,
        brands=brands,
        category_paths=category_paths,
        extraction_frequency=extraction_frequency,
        source_titles=source_titles,
        trend=trend,
    )


def _chunks(values: list[str], size: int) -> list[list[str]]:
    return [values[index : index + size] for index in range(0, len(values), size)]


def _guess_source_category(category_path: str) -> str:
    if "자동차" in category_path:
        return "자동차용품"
    if "캠핑" in category_path or "레저" in category_path:
        return "캠핑용품"
    if "생활" in category_path or "주방" in category_path or "욕실" in category_path:
        return "생활용품"
    return ""

