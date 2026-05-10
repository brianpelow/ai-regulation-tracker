"""Regulatory feed sources for AI Regulation Tracker."""

from __future__ import annotations

import httpx
import feedparser
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta


@dataclass
class RegulatoryItem:
    """A single regulatory development."""
    title: str
    url: str
    agency: str
    summary: str = ""
    published: str = ""
    relevance_score: float = 0.0
    ai_relevant: bool = False


FEEDS = [
    ("OCC", "https://www.occ.gov/news-issuances/rss/occ-news.xml"),
    ("Federal Reserve", "https://www.federalreserve.gov/feeds/press_all.xml"),
    ("CFPB", "https://www.consumerfinance.gov/about-us/newsroom/feed/"),
    ("FDIC", "https://www.fdic.gov/news/press-releases/rss.xml"),
    ("SEC", "https://www.sec.gov/rss/news/press.xml"),
    ("FCA", "https://www.fca.org.uk/news/rss.xml"),
    ("ECB", "https://www.ecb.europa.eu/rss/press.html"),
]

AI_KEYWORDS = [
    "artificial intelligence", "machine learning", "AI", "automated decision",
    "algorithmic", "model risk", "explainability", "model governance",
    "automated underwriting", "credit model", "fair lending algorithm",
    "AI governance", "model validation", "automated valuation",
    "predictive model", "neural network", "large language model", "LLM",
    "generative AI", "GenAI", "AI Act", "model risk management",
    "SR 11-7", "OCC 2011-12", "automated system", "decision engine",
    "risk model", "compliance automation", "RegTech", "SupTech",
]

HORIZON_KEYWORDS = [
    "proposed rule", "comment period", "request for information", "RFI",
    "advance notice", "ANPR", "notice of proposed", "final rule",
    "effective date", "compliance date", "examination guidance",
    "supervisory letter", "interagency", "consultation paper",
]


def fetch_all_feeds(max_age_days: int = 7) -> list[RegulatoryItem]:
    """Fetch items from all regulatory RSS feeds."""
    items = []
    cutoff = datetime.now(timezone.utc) - timedelta(days=max_age_days)

    for agency, url in FEEDS:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:15]:
                title = entry.get("title", "").strip()
                link = entry.get("link", "").strip()
                summary = entry.get("summary", entry.get("description", ""))[:600]
                published = entry.get("published", "")

                if title and link:
                    items.append(RegulatoryItem(
                        title=title,
                        url=link,
                        agency=agency,
                        summary=summary,
                        published=published,
                    ))
        except Exception as e:
            print(f"[sources] Failed to fetch {agency}: {e}")
            continue

    return items


def fetch_eu_ai_act() -> list[RegulatoryItem]:
    """Fetch EU AI Act developments."""
    items = []
    try:
        with httpx.Client(timeout=15) as client:
            r = client.get(
                "https://hn.algolia.com/api/v1/search",
                params={
                    "query": "EU AI Act regulation enforcement",
                    "tags": "story",
                    "numericFilters": f"created_at_i>{int((datetime.now(timezone.utc) - timedelta(days=7)).timestamp())}",
                    "hitsPerPage": 5,
                }
            )
            if r.status_code == 200:
                for hit in r.json().get("hits", []):
                    title = hit.get("title", "")
                    url = hit.get("url") or f"https://news.ycombinator.com/item?id={hit.get('objectID')}"
                    if title and any(kw.lower() in title.lower() for kw in ["AI Act", "EU AI", "artificial intelligence act"]):
                        items.append(RegulatoryItem(
                            title=title,
                            url=url,
                            agency="EU / HackerNews",
                            summary=f"HN points: {hit.get('points', 0)}",
                        ))
    except Exception as e:
        print(f"[sources] EU AI Act fetch failed: {e}")
    return items


def is_ai_relevant(item: RegulatoryItem) -> bool:
    """Check if an item is relevant to AI/ML governance."""
    text = (item.title + " " + item.summary).lower()
    return any(kw.lower() in text for kw in AI_KEYWORDS)


def is_horizon_item(item: RegulatoryItem) -> bool:
    """Check if an item is forward-looking (proposed rules, comment periods)."""
    text = (item.title + " " + item.summary).lower()
    return any(kw.lower() in text for kw in HORIZON_KEYWORDS)


def gather_all() -> tuple[list[RegulatoryItem], list[RegulatoryItem]]:
    """Gather all items, return (current, horizon) lists."""
    all_items = fetch_all_feeds() + fetch_eu_ai_act()
    ai_items = [i for i in all_items if is_ai_relevant(i)]
    horizon = [i for i in ai_items if is_horizon_item(i)]
    current = [i for i in ai_items if not is_horizon_item(i)]
    return current[:8], horizon[:4]