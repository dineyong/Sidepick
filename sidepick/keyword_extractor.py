from __future__ import annotations

import html
import re
from collections import Counter
from dataclasses import dataclass


TAG_RE = re.compile(r"<[^>]+>")
TOKEN_RE = re.compile(r"[가-힣A-Za-z0-9]+")

STOPWORDS = {
    "무료배송",
    "국내배송",
    "당일배송",
    "오늘출발",
    "정품",
    "공식",
    "브랜드",
    "신상",
    "추천",
    "세트",
    "묶음",
    "대용량",
    "특가",
    "할인",
    "모음",
    "택배",
    "주문",
    "쿠폰",
    "증정",
    "네이버",
    "스마트스토어",
}

GENERIC_SINGLE_WORDS = {
    "용품",
    "생활",
    "자동차",
    "차량",
    "캠핑",
    "주방",
    "욕실",
    "청소",
    "수납",
}


@dataclass(frozen=True)
class ExtractedKeyword:
    keyword: str
    frequency: int
    source_titles: int


def clean_title(title: str) -> str:
    title = TAG_RE.sub(" ", title)
    title = html.unescape(title)
    title = re.sub(r"[\[\]()/,+|·:;_-]+", " ", title)
    return re.sub(r"\s+", " ", title).strip()


def tokenize(title: str) -> list[str]:
    tokens = [match.group(0).lower() for match in TOKEN_RE.finditer(clean_title(title))]
    filtered = []
    for token in tokens:
        if len(token) <= 1:
            continue
        if token.isdigit():
            continue
        if token in STOPWORDS:
            continue
        filtered.append(token)
    return filtered


def extract_keywords(
    titles: list[str],
    min_frequency: int = 2,
    limit: int = 30,
) -> list[ExtractedKeyword]:
    phrase_counts: Counter[str] = Counter()
    title_presence: dict[str, set[int]] = {}

    for title_index, title in enumerate(titles):
        tokens = tokenize(title)
        seen_in_title = set()
        for n in (1, 2, 3):
            if len(tokens) < n:
                continue
            for index in range(0, len(tokens) - n + 1):
                phrase_tokens = tokens[index : index + n]
                phrase = " ".join(phrase_tokens)
                if phrase in STOPWORDS:
                    continue
                if n == 1 and phrase in GENERIC_SINGLE_WORDS:
                    continue
                if len(phrase.replace(" ", "")) < 3:
                    continue
                phrase_counts[phrase] += 1
                seen_in_title.add(phrase)
        for phrase in seen_in_title:
            title_presence.setdefault(phrase, set()).add(title_index)

    candidates = []
    for phrase, frequency in phrase_counts.items():
        source_titles = len(title_presence.get(phrase, set()))
        if frequency < min_frequency or source_titles < min_frequency:
            continue
        candidates.append(ExtractedKeyword(phrase, frequency, source_titles))

    candidates.sort(
        key=lambda item: (
            item.source_titles,
            item.frequency,
            len(item.keyword.split()),
            len(item.keyword),
        ),
        reverse=True,
    )
    return candidates[:limit]

