from __future__ import annotations

from datetime import date, timedelta
from typing import Iterable

import requests


SHOPPING_SEARCH_URL = "https://openapi.naver.com/v1/search/shop.json"
SHOPPING_INSIGHT_KEYWORDS_URL = (
    "https://openapi.naver.com/v1/datalab/shopping/category/keywords"
)


class NaverApiError(RuntimeError):
    pass


class NaverClient:
    def __init__(self, client_id: str, client_secret: str) -> None:
        self.headers = {
            "X-Naver-Client-Id": client_id,
            "X-Naver-Client-Secret": client_secret,
        }

    def _raise_for_response(self, response: requests.Response) -> None:
        if response.ok:
            return
        raise NaverApiError(
            f"Naver API request failed: {response.status_code} {response.text[:500]}"
        )

    def search_shop(
        self,
        query: str,
        display: int = 50,
        start: int = 1,
        sort: str = "sim",
        exclude: str = "used:rental:cbshop",
    ) -> dict:
        params = {
            "query": query,
            "display": max(1, min(display, 100)),
            "start": max(1, min(start, 1000)),
            "sort": sort,
            "exclude": exclude,
        }
        response = requests.get(
            SHOPPING_SEARCH_URL,
            headers=self.headers,
            params=params,
            timeout=20,
        )
        self._raise_for_response(response)
        return response.json()

    def shopping_keyword_trends(
        self,
        category_id: str,
        keywords: Iterable[str],
        weeks: int = 8,
    ) -> dict:
        end = date.today() - timedelta(days=1)
        start = end - timedelta(weeks=weeks)
        keyword_groups = [
            {"name": keyword[:60], "param": [keyword]}
            for keyword in keywords
        ]
        payload = {
            "startDate": start.isoformat(),
            "endDate": end.isoformat(),
            "timeUnit": "week",
            "category": category_id,
            "keyword": keyword_groups,
            "device": "",
            "gender": "",
            "ages": [],
        }
        response = requests.post(
            SHOPPING_INSIGHT_KEYWORDS_URL,
            headers={**self.headers, "Content-Type": "application/json"},
            json=payload,
            timeout=20,
        )
        self._raise_for_response(response)
        return response.json()

