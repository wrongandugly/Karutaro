#!/usr/bin/env python3
"""Karutaro WAVE tool (Crawl4AI, Apache-2.0, plugged 2026-11-28).

Sweeps ONE official site whole and saves every page's clean
markdown into wave-result.json. Equipment for the directory
reading waves - NOT part of the daily hunt (the hunt stays lean).
Triggered by a push of wave-request.json:
    {"url": "https://example.jp/", "max_pages": 10}
Depth 1 from the seed, same-site links only.
"""
import asyncio
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

BASE = Path(__file__).resolve().parent
JST = timezone(timedelta(hours=9))


async def run():
    req = json.loads((BASE / "wave-request.json").read_text(
        encoding="utf-8"))
    url = req["url"]
    max_pages = int(req.get("max_pages", 10))
    from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
    from crawl4ai.deep_crawling import BFSDeepCrawlStrategy
    config = CrawlerRunConfig(
        deep_crawl_strategy=BFSDeepCrawlStrategy(
            max_depth=1, max_pages=max_pages, include_external=False))
    pages = []
    async with AsyncWebCrawler() as crawler:
        results = await crawler.arun(url=url, config=config)
        if not isinstance(results, list):
            results = [results]
        for r in results:
            md = getattr(r, "markdown", "")
            pages.append({
                "url": getattr(r, "url", url),
                "ok": bool(getattr(r, "success", False)),
                "markdown": str(md or "")[:20000],
            })
    out = {"at": datetime.now(JST).isoformat(timespec="seconds"),
           "seed": url, "pages": pages}
    (BASE / "wave-result.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1),
        encoding="utf-8")
    print(f"wave: {len(pages)} pages, "
          f"{sum(1 for p in pages if p['ok'])} ok")


if __name__ == "__main__":
    asyncio.run(run())
