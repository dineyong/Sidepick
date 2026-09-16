from __future__ import annotations

import math
import statistics
from dataclasses import dataclass


@dataclass(frozen=True)
class CandidateMetrics:
    keyword: str
    total_results: int
    prices: list[int]
    brands: set[str]
    category_paths: list[str]
    extraction_frequency: int
    source_titles: int
    trend: list[dict]


def summarize_candidate(metrics: CandidateMetrics) -> dict:
    prices = [price for price in metrics.prices if price and price > 0]
    avg_price = statistics.mean(prices) if prices else None
    median_price = statistics.median(prices) if prices else None
    return {
        "avg_price": avg_price,
        "median_price": median_price,
        "min_price": min(prices) if prices else None,
        "max_price": max(prices) if prices else None,
        "brand_count": len({brand for brand in metrics.brands if brand}),
        "category_path": most_common(metrics.category_paths),
    }


def score_candidates(metrics_list: list[CandidateMetrics]) -> list[dict]:
    max_latest = max((_latest_ratio(item.trend) for item in metrics_list), default=0.0)
    min_log_total = min((_safe_log(item.total_results) for item in metrics_list), default=0.0)
    max_log_total = max((_safe_log(item.total_results) for item in metrics_list), default=1.0)
    total_span = max(max_log_total - min_log_total, 1.0)

    scored = []
    for metrics in metrics_list:
        summary = summarize_candidate(metrics)
        latest_ratio = _latest_ratio(metrics.trend)
        trend_change_pct = _trend_change_pct(metrics.trend)
        trend_score = _trend_score(latest_ratio, trend_change_pct, max_latest)
        competition_score = _competition_score(metrics.total_results, min_log_total, total_span)
        price_score = _price_score(summary["median_price"])
        persistence_score = _persistence_score(metrics.trend)
        total_score = trend_score + competition_score + price_score + persistence_score

        scored.append(
            {
                "candidate_keyword": metrics.keyword,
                "extraction_frequency": metrics.extraction_frequency,
                "source_titles": metrics.source_titles,
                "total_results": metrics.total_results,
                **summary,
                "latest_trend_ratio": latest_ratio if metrics.trend else None,
                "trend_change_pct": trend_change_pct if metrics.trend else None,
                "trend_points": len(metrics.trend),
                "score_components": {
                    "demand_trend": round(trend_score, 2),
                    "competition": round(competition_score, 2),
                    "price": round(price_score, 2),
                    "persistence": round(persistence_score, 2),
                },
                "sidepick_score": round(max(0.0, min(100.0, total_score)), 2),
                "reason": build_reason(
                    metrics,
                    trend_score,
                    competition_score,
                    price_score,
                    persistence_score,
                    trend_change_pct,
                    summary["median_price"],
                ),
            }
        )

    scored.sort(key=lambda row: row["sidepick_score"], reverse=True)
    return scored


def build_reason(
    metrics: CandidateMetrics,
    trend_score: float,
    competition_score: float,
    price_score: float,
    persistence_score: float,
    trend_change_pct: float,
    median_price: float | None,
) -> str:
    reasons = [
        f"상품명 {metrics.source_titles}개에서 반복 등장",
        f"검색 결과 {metrics.total_results:,}건 기준 경쟁도 점수 {competition_score:.1f}/30",
    ]
    if metrics.trend:
        direction = "상승" if trend_change_pct > 0 else "하락" if trend_change_pct < 0 else "보합"
        reasons.append(f"최근 클릭 추이 {direction}({trend_change_pct:.1f}%)")
    else:
        reasons.append("DataLab 카테고리 코드/응답 없음으로 트렌드 점수 제외")
    if median_price:
        reasons.append(f"중앙가격 {median_price:,.0f}원, 가격 매력도 {price_score:.1f}/20")
    if persistence_score > 0:
        reasons.append(f"추세 지속성 {persistence_score:.1f}/10")
    if trend_score == 0 and not metrics.trend:
        reasons.append("점수는 상품/가격/경쟁 데이터 중심")
    return "; ".join(reasons)


def most_common(values: list[str]) -> str:
    counts: dict[str, int] = {}
    for value in values:
        if not value:
            continue
        counts[value] = counts.get(value, 0) + 1
    if not counts:
        return ""
    return max(counts.items(), key=lambda item: item[1])[0]


def _latest_ratio(trend: list[dict]) -> float:
    if not trend:
        return 0.0
    return float(trend[-1].get("ratio", 0.0))


def _trend_change_pct(trend: list[dict]) -> float:
    if len(trend) < 4:
        return 0.0
    ratios = [float(point.get("ratio", 0.0)) for point in trend]
    previous = ratios[-4:-2]
    recent = ratios[-2:]
    previous_avg = sum(previous) / len(previous)
    recent_avg = sum(recent) / len(recent)
    if previous_avg <= 0:
        return 0.0
    return ((recent_avg - previous_avg) / previous_avg) * 100


def _trend_score(latest_ratio: float, trend_change_pct: float, max_latest: float) -> float:
    if max_latest <= 0:
        return 0.0
    latest_component = (latest_ratio / max_latest) * 26
    change_component = max(-1.0, min(trend_change_pct / 50, 1.0)) * 14
    return max(0.0, min(40.0, latest_component + max(0.0, change_component)))


def _safe_log(value: int) -> float:
    return math.log10(max(value, 1))


def _competition_score(total_results: int, min_log_total: float, total_span: float) -> float:
    normalized = (_safe_log(total_results) - min_log_total) / total_span
    return max(0.0, min(30.0, (1.0 - normalized) * 30))


def _price_score(median_price: float | None) -> float:
    if median_price is None or median_price <= 0:
        return 0.0
    if 10_000 <= median_price <= 80_000:
        return 20.0
    if 5_000 <= median_price < 10_000:
        return 12.0 + ((median_price - 5_000) / 5_000) * 8.0
    if 80_000 < median_price <= 150_000:
        return 20.0 - ((median_price - 80_000) / 70_000) * 8.0
    if 150_000 < median_price <= 300_000:
        return 8.0
    return 4.0


def _persistence_score(trend: list[dict]) -> float:
    if len(trend) < 4:
        return 0.0
    ratios = [float(point.get("ratio", 0.0)) for point in trend]
    non_declining = 0
    comparisons = 0
    for previous, current in zip(ratios, ratios[1:]):
        comparisons += 1
        if current >= previous * 0.95:
            non_declining += 1
    if comparisons == 0:
        return 0.0
    return (non_declining / comparisons) * 10

