#!/usr/bin/env python3
"""HOSIKO hunter robot — PROCURO prototype v0.

Reads the active want from want.json, sweeps public Japanese marketplaces
(read-only, gentle rate), classifies what it finds into honesty tiers
(confirmed fits / near-misses over the ceiling / unconfirmed fitment /
discard examples — every shown discard carries its reason), tops the
delivery with a rule-built verdict summary (the resuminho), and writes
it all to results.json. No LLM calls. One source failing never
kills the run.
"""
import json, re, sys, time, urllib.error, urllib.parse, urllib.request
from datetime import datetime, timezone, timedelta
from html import unescape
from pathlib import Path

BASE = Path(__file__).resolve().parent
WANT_FILE = BASE / "want.json"
RESULTS_FILE = BASE / "results.json"
WANTS_FILE = BASE / "wants.json"
BOARD_FILE = BASE / "board.json"
LOG_FILE = BASE / "hunter.log"

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")
JST = timezone(timedelta(hours=9))
REQ_TIMEOUT = 25
SLEEP_BETWEEN = 1.2  # gentle rate


def log(msg):
    line = f"[{datetime.now(JST).isoformat(timespec='seconds')}] {msg}"
    print(line, flush=True)
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except OSError:
        pass


def fetch(url):
    req = urllib.request.Request(url, headers={
        "User-Agent": UA,
        "Accept-Language": "ja,en;q=0.8",
    })
    with urllib.request.urlopen(req, timeout=REQ_TIMEOUT) as r:
        raw = r.read()
    return raw.decode("utf-8", "replace")


def norm(s):
    return re.sub(r"\s+", " ", (s or "").lower()).strip()


def tokens_of(text):
    parts = re.split(r"[\s　,、/・]+", norm(text))
    return [p for p in parts if len(p) >= 2]


# ---------------- sources ----------------

def sweep_yahoo(queries):
    """Yahoo! Auctions search — items embedded in __NEXT_DATA__ JSON."""
    items, seen = [], set()
    for q in queries[:3]:
        url = "https://auctions.yahoo.co.jp/search/search?p=" + urllib.parse.quote(q)
        html = fetch(url)
        m = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>',
                      html, re.S)
        if not m:
            raise RuntimeError("NEXT_DATA not found")
        data = json.loads(m.group(1))
        found = []

        def walk(o):
            if isinstance(o, dict):
                if "auctionId" in o and "title" in o:
                    found.append(o)
                for v in o.values():
                    walk(v)
            elif isinstance(o, list):
                for v in o:
                    walk(v)

        walk(data)
        for it in found:
            aid = it.get("auctionId")
            if not aid or aid in seen:
                continue
            seen.add(aid)
            price = it.get("price")
            items.append({
                "title": unescape(it.get("title") or "").strip(),
                "price": int(price) if isinstance(price, (int, float)) else None,
                "url": f"https://auctions.yahoo.co.jp/jp/auction/{aid}",
                "image": it.get("imageUrl") or None,
                "source": "Yahoo! Auctions",
                "kind": "auction",
            })
        time.sleep(SLEEP_BETWEEN)
    return items


def raw_tokens(text):
    parts = re.split(r"[\s　,、/・]+", (text or "").strip())
    return [p for p in parts if len(p) >= 2]


def sweep_jimoty(queries):
    """Jimoty keyword pages — /all/sale-kw-<keyword> is a pre-built landing
    page that exists ONLY for keywords in Jimoty's index (Nintendo, キャリア,
    ルーフキャリア...). A non-indexed keyword (CX-5, iPhone, スキー...) returns
    HTTP 404 — that is normal, not an outage: skip it and try the next
    keyword. (The live /all/search endpoint answers 404/timeout to plain
    HTTP clients from this VM, so the indexed kw pages are the viable
    route.) The old version let the first keyword's 404 kill the source."""
    items, seen = [], set()
    kws = []
    for q in queries:
        for tok in raw_tokens(q):
            if tok not in kws:
                kws.append(tok)
    if not kws and queries:
        kws = [queries[0]]
    ok_pages, hard_errors = 0, []
    for kw in kws[:3]:
        url = "https://jmty.jp/all/sale-kw-" + urllib.parse.quote(kw)
        try:
            html = fetch(url)
        except urllib.error.HTTPError as e:
            if e.code == 404:
                continue  # keyword not indexed by Jimoty — skip, keep going
            hard_errors.append(f"{kw}: HTTP {e.code}")
            continue
        ok_pages += 1
        blocks = re.split(r"p-articles-list-item", html)[1:]
        for b in blocks:
            m = re.search(r'href="(https://jmty\.jp/[a-z]+/sale-[a-z-]+/article-[a-z0-9]+)"', b)
            if not m:
                continue
            link = m.group(1)
            if link in seen:
                continue
            seen.add(link)
            tm = re.search(r'p-item-title["\']>\s*<a[^>]*>(.*?)</a>', b, re.S)
            title = unescape(re.sub(r"<[^>]+>", "", tm.group(1))).strip() if tm else ""
            pm = re.search(r'p-item-most-important["\']>\s*<b>([\d,]+)円</b>', b)
            price = int(pm.group(1).replace(",", "")) if pm else None
            if pm is None and "無料" in b[:2000]:
                price = 0
            im = re.search(r'<img[^>]+src="(https://cdn\.jmty\.jp/[^"]+)"', b)
            items.append({
                "title": title,
                "price": price,
                "url": link,
                "image": im.group(1) if im else None,
                "source": "Jimoty",
                "kind": "classified",
            })
        time.sleep(SLEEP_BETWEEN)
    if not ok_pages and hard_errors:
        raise RuntimeError("no keyword page reachable: " + "; ".join(hard_errors))
    return items


def sweep_upgarage(queries):
    """Up Garage — the EC site is a Nuxt SPA (the /ec/search HTML is an
    empty shell), but the app is backed by a public JSON API:
    GET www.upgarage.com/service/api/v1/items?search_word=<q>
    (the keyword parameter is 'search_word'; 'keyword'/'name'/'q' are
    silently ignored and return the whole catalogue). Price uses
    tax_included_price — what the buyer actually pays."""
    items, seen = [], set()
    for q in queries[:3]:
        url = ("https://www.upgarage.com/service/api/v1/items?limit=40&search_word="
               + urllib.parse.quote(q))
        req = urllib.request.Request(url, headers={
            "User-Agent": UA,
            "Accept": "application/json",
            "Accept-Language": "ja,en;q=0.8",
        })
        with urllib.request.urlopen(req, timeout=REQ_TIMEOUT) as r:
            data = json.loads(r.read().decode("utf-8", "replace"))
        for it in data.get("resources", []):
            iid = str(it.get("id") or "")
            if not iid or iid in seen:
                continue
            seen.add(iid)
            price = it.get("tax_included_price")
            if price is None:
                price = it.get("price")
            item = {
                "title": unescape(it.get("name") or "").strip(),
                "price": int(price) if isinstance(price, (int, float)) else None,
                "url": f"https://www.upgarage.com/ec/item/{iid}",
                "image": it.get("image_url") or None,
                "source": "Up Garage",
                "kind": "shop",
                "item_id": iid,
            }
            if it.get("shop_name"):
                item["shop"] = it["shop_name"]
            apply_upgarage_auction(item, it)
            items.append(item)
        time.sleep(SLEEP_BETWEEN)
    return items


def apply_upgarage_auction(item, res):
    """Up Garage sells fixed-price AND runs auctions on the same shelf.
    A record with auction_details (detail endpoint) or auction fields
    (search payload) is an AUCTION — never a 'shop'. When a buyout price
    exists, the record's listed price IS that buyout (verified on item
    23335899: price ¥2,860 = tax_included_buyout_price, bid was ¥1).
    Records kind / buyout / end_time on the item, in place."""
    det = res.get("auction_details")
    if not isinstance(det, dict):
        det = None
    if det:
        buyout = det.get("tax_included_buyout_price")
        if buyout is None:
            buyout = det.get("buyout_price")
        end_time = det.get("end_time")
        is_auction = True
    else:
        buyout = res.get("tax_included_buyout_price")
        if buyout is None:
            buyout = res.get("buyout_price")
        end_time = res.get("auction_end_time")
        is_auction = (end_time is not None or buyout is not None
                      or res.get("bid_price") is not None)
    if not is_auction:
        return
    item["kind"] = "auction"
    if isinstance(buyout, (int, float)):
        item["buyout"] = int(buyout)
    if end_time:
        item["end_time"] = end_time


def enrich_upgarage(item):
    """Fetch the detail record for a SHOWN Up Garage item: authoritative
    shop name, auction details, and the seller's own description — the
    only place '本体のみ' (unit only: no keys/bolts) is ever stated.
    Failure leaves the item untouched; the verdict rules then simply
    know less about it and say less."""
    iid = item.get("item_id")
    if not iid:
        return
    url = f"https://www.upgarage.com/service/api/v1/items/{iid}"
    req = urllib.request.Request(url, headers={
        "User-Agent": UA,
        "Accept": "application/json",
        "Accept-Language": "ja,en;q=0.8",
    })
    try:
        with urllib.request.urlopen(req, timeout=REQ_TIMEOUT) as r:
            res = json.loads(r.read().decode("utf-8", "replace")).get("resources", {})
    except Exception as e:  # enrichment is best-effort, never fatal
        log(f"Up Garage detail {iid}: FAILED {type(e).__name__}: {e}")
        return
    shop = (res.get("shop") or {}).get("name")
    if shop:
        item["shop"] = shop
    apply_upgarage_auction(item, res)
    desc = res.get("detailed_explanation") or ""
    if desc:
        item["unit_only"] = "本体のみ" in desc
        item["has_keys"] = "鍵" in desc
        item["has_bolts"] = ("ボルト" in desc) or ("ナット" in desc)
    time.sleep(SLEEP_BETWEEN)


def sweep_yahoo_furima(queries):
    """Yahoo!フリマ (ex-PayPayフリマ) — the search page is server-rendered;
    each item anchor's text carries 'price 円 いいね！ title' plus an img."""
    items, seen = [], set()
    for q in queries[:3]:
        url = ("https://paypayfleamarket.yahoo.co.jp/search/"
               + urllib.parse.quote(q, safe=""))
        html = fetch(url)
        anchors = re.findall(r'<a[^>]+href="/item/([a-z0-9]+)"[^>]*>(.*?)</a>',
                             html, re.S)
        if not anchors:
            raise RuntimeError("no item anchors in response (bot wall or layout change)")
        for iid, body in anchors:
            if iid in seen:
                continue
            text = unescape(re.sub(r"<[^>]+>", " ", body))
            text = re.sub(r"\s+", " ", text).strip()
            pm = re.search(r"([\d,]+)\s*円", text)
            price = int(pm.group(1).replace(",", "")) if pm else None
            title = text[pm.end():].strip() if pm else text
            title = re.sub(r"^いいね！\s*", "", title).strip()
            if not title:
                continue
            seen.add(iid)
            im = re.search(r'<img[^>]+src="([^"]+)"', body)
            items.append({
                "title": title,
                "price": price,
                "url": f"https://paypayfleamarket.yahoo.co.jp/item/{iid}",
                "image": unescape(im.group(1)) if im else None,
                "source": "Yahoo!フリマ",
                "kind": "classified",
            })
        time.sleep(SLEEP_BETWEEN)
    return items


def sweep_rakuten(queries):
    """Rakuten Ichiba search (often bot-walled; failure is tolerated)."""
    items, seen = [], set()
    for q in queries[:3]:
        url = "https://search.rakuten.co.jp/search/mall/" + urllib.parse.quote(q) + "/"
        html = fetch(url)
        if "item.rakuten.co.jp" not in html:
            raise RuntimeError("no item links in response (bot wall or empty shell)")
        for m in re.finditer(
                r'href="(https://item\.rakuten\.co\.jp/[^"]+)"[^>]*>([^<]{4,120})</a>', html):
            link, title = m.group(1), unescape(m.group(2)).strip()
            if link in seen:
                continue
            seen.add(link)
            window = html[m.end(): m.end() + 1500]
            pm = re.search(r'([\d,]+)円', window)
            items.append({
                "title": title,
                "price": int(pm.group(1).replace(",", "")) if pm else None,
                "url": link,
                "image": None,
                "source": "Rakuten",
                "kind": "shop",
            })
        time.sleep(SLEEP_BETWEEN)
    return items


def sweep_mercari(queries):
    """Mercari — the search page is a JS app fed by api.mercari.jp JSON
    (prices in JPY). A real Chromium (Playwright) loads the page and we
    harvest the API responses. DOM fallback keeps only yen-priced cards:
    a price shown in another currency is never converted or guessed.
    Raises when Playwright/Chromium is unavailable — the run tolerates
    a failed source by design."""
    from playwright.sync_api import sync_playwright
    items, seen = [], set()

    def harvest(o):
        if isinstance(o, dict):
            name = o.get("name")
            price = o.get("price")
            iid = o.get("id")
            if (isinstance(name, str) and name.strip()
                    and isinstance(price, (int, float))
                    and isinstance(iid, str) and iid.startswith("m")
                    and len(iid) >= 6):
                status = str(o.get("status") or "").lower()
                if "sold" not in status and iid not in seen:
                    seen.add(iid)
                    img = None
                    th = o.get("thumbnails")
                    if isinstance(th, list) and th and isinstance(th[0], str):
                        img = th[0]
                    items.append({
                        "title": unescape(name).strip(),
                        "price": int(price),
                        "url": f"https://jp.mercari.com/item/{iid}",
                        "image": img,
                        "source": "Mercari",
                        "kind": "classified",
                    })
            for v in o.values():
                harvest(v)
        elif isinstance(o, list):
            for v in o:
                harvest(v)

    captured = []

    with sync_playwright() as p:
        b = p.chromium.launch(headless=True,
                              args=["--no-sandbox", "--lang=ja-JP"])
        pg = b.new_page(locale="ja-JP", timezone_id="Asia/Tokyo",
                        user_agent=UA)

        def on_response(resp):
            try:
                if ("mercari" in resp.url and resp.status == 200
                        and ("api" in resp.url or "search" in resp.url)):
                    captured.append(resp.json())
            except Exception:
                pass

        pg.on("response", on_response)
        for q in queries[:2]:
            url = ("https://jp.mercari.com/search?keyword="
                   + urllib.parse.quote(q))
            pg.goto(url, wait_until="domcontentloaded", timeout=60000)
            try:
                pg.wait_for_selector('a[href*="/item/"]', timeout=20000)
            except Exception:
                pass
            pg.wait_for_timeout(2500)
            for data in captured:
                harvest(data)
            captured.clear()
            if not items:
                anchors = pg.query_selector_all('a[href*="/item/"]')
                for a in anchors:
                    href = a.get_attribute("href") or ""
                    m = re.search(r"/item/(m\w+)", href)
                    if not m or m.group(1) in seen:
                        continue
                    txt = re.sub(r"\s+", " ",
                                 (a.inner_text() or "")).strip()
                    pm = re.search(r"¥\s*([\d,]+)", txt)
                    if not pm:
                        continue
                    title = (txt[pm.end():].strip(" 　")
                             or txt[:pm.start()].strip())
                    if not title:
                        continue
                    seen.add(m.group(1))
                    items.append({
                        "title": title,
                        "price": int(pm.group(1).replace(",", "")),
                        "url": "https://jp.mercari.com/item/" + m.group(1),
                        "image": None,
                        "source": "Mercari",
                        "kind": "classified",
                    })
            time.sleep(SLEEP_BETWEEN)
        b.close()
    if not items:
        raise RuntimeError("no Mercari items captured "
                           "(API shape changed or bot wall)")
    return items


SOURCES = [
    ("Yahoo! Auctions", sweep_yahoo),
    ("Yahoo!フリマ", sweep_yahoo_furima),
    ("Jimoty", sweep_jimoty),
    ("Up Garage", sweep_upgarage),
    ("Mercari", sweep_mercari),
    ("Rakuten", sweep_rakuten),
]



# ---------------- fitment profiles (instructor-taught) ----------------
# Fabricio's correction (2026-11-22): the spec is FITMENT, not the literal
# string. A carrier that FITS his CX-5 (KE generation, 2015) is valid even
# if the title never says "CX-5" — and a title that never states fitment
# must NEVER be presented as a confirmed fit. Profiles are taught per
# want-key by the instructor; wants without a profile keep the plain
# token matching (classify_generic below).

FITMENT_PROFILES = {
    "cx-5": {
        # extra sweep queries, fitment-oriented (added to the want's own)
        "queries": ["KE系 キャリア", "CX-5 ルーフキャリア", "マツダ ベースキャリア"],
        # title states fitment for this car
        "fit_markers": ["cx-5", "cx5", "ke系", "ke2"],
        # title states the make but not the model
        "make_markers": ["マツダ", "mazda"],
        # title states fitment for a DIFFERENT model of the same make
        "other_models": ["デミオ", "demio", "アクセラ", "axela", "アテンザ", "atenza",
                         "フレア", "cx-3", "cx3", "cx-30", "cx-8", "cx8", "cx-7",
                         "cx7", "ロードスター", "プレマシー", "ビアンテ", "rx-8", "mpv"],
        # title mentions a base / full system (kills the "attachment only" read)
        "base_markers": ["ベースキャリア", "ルーフキャリア", "キャリアベース",
                         "ルーフラック", "ベース付", "フット付"],
        # title is about roof carrying at all (no bare "バー": it hides
        # inside カバー "cover" and ナンバー "number plate")
        "kind_markers": ["キャリア", "ルーフラック", "ベース", "フット"],
        # title is the snowboard/ski ATTACHMENT (mounts ON a base)
        "attach_markers": ["スキーキャリア", "スノーボードキャリア", "スノーキャリア",
                           "スキーアタッチメント", "スノーボードアタッチメント",
                           "アタッチメント", "スキーホルダー", "スノーボードホルダー"],
        # title is only the vehicle-specific HOOK kit (a part, not a system),
        # unless it also names the system/bars it belongs to
        "hook_markers": ["フック"],
        "hook_safe": ["システムキャリア", "ベースキャリア", "ルーフキャリア",
                      "キャリアセット", "フルセット", "バー"],
        "car_label": "CX-5 (KE)",
    },
}


def fitment_profile_for(want):
    hay = norm((want.get("what") or "") + " " + (want.get("details") or ""))
    for key, prof in FITMENT_PROFILES.items():
        if key in hay:
            return prof
    return None


def classify_with_profile(it, t, prof, ceiling):
    """Honesty tiers for a profiled want. Returns (tier, reason-PT-or-None,
    example_priority); tier in fit / near / unconfirmed / example / reject.
    Fitment stated is never enough on its own: the title must also be about
    a carrier (kind gate) — a brake pad that says CX-5 is not a near-miss."""
    price = it["price"]
    car = prof["car_label"]
    if "ヒッチ" in t:
        return "reject", None, 0  # rear-hitch carrier — wrong mounting entirely
    has_fit = any(m in t for m in prof["fit_markers"])
    has_make = any(m in t for m in prof["make_markers"])
    other = next((m for m in prof["other_models"] if m in t), None)
    attach_only = (any(m in t for m in prof["attach_markers"])
                   and not any(m in t for m in prof["base_markers"]))
    hook_only = (any(m in t for m in prof["hook_markers"])
                 and not any(m in t for m in prof["hook_safe"]))
    kind_ok = any(m in t for m in prof["kind_markers"])
    if attach_only:
        # e.g. a THULE snow carrier: it is the attachment only, no base —
        # useless to a buyer who owns no base yet, whatever the title says.
        return "example", ("parece ser só o acessório de prancha, sem a base — "
                           "e você ainda não tem a base"), 0
    if hook_only:
        return "example", ("parece ser só o kit de ganchos de fixação (フック), "
                           "sem as barras — não é o sistema completo"), 2
    if "フットセット" in t and not any(m in t for m in prof["hook_safe"]):
        return "example", ("parece ser só o conjunto de pés de fixação "
                           "(フットセット), sem as barras — não é o sistema "
                           "completo"), 2
    if "ネット" in t and not any(m in t for m in ("ベースキャリア", "システムキャリア",
                                                  "ルーフラック")):
        return "reject", None, 0  # a cargo net for a carrier — not a carrier
    if not kind_ok:
        return "reject", None, 0
    if other and not has_fit:
        return "example", f"o título indica outro modelo ({other}) — não é pra {car}", 1
    if has_fit:
        if ceiling is not None and price is not None and price > ceiling:
            return "near", f"passou do teto em ¥{price - ceiling:,}", 0
        return "fit", None, 0
    if has_make:
        reason = (f"o título diz Mazda, mas não diz o modelo — "
                  f"precisa conferir se é da {car}")
    else:
        reason = (f"o título não confirma se serve na {car} — "
                  "precisa conferir o encaixe")
    if ceiling is not None and price is not None and price > ceiling:
        reason += f"; também passou do teto em ¥{price - ceiling:,}"
    return "unconfirmed", reason, 0


def classify_generic(it, t, what_toks, phrase, ceiling):
    """Plain token matching for wants without a fitment profile.
    Returns (tier, reason-PT-or-None, example_priority);
    tier in fit / near / example / reject."""
    price = it["price"]
    if what_toks:
        missing = [tok for tok in what_toks if tok not in t]
        matched = len(what_toks) - len(missing)
    else:
        missing = [] if phrase in t else [phrase]
        matched = 0 if missing else 1
    if not missing:
        if ceiling is not None and price is not None and price > ceiling:
            return "near", f"passou do teto em ¥{price - ceiling:,}", 0
        return "fit", None, 0
    if matched >= 1:
        return "example", f"o título não menciona '{missing[0]}'", 0
    return "reject", None, 0


# ---------------- verdict (the resuminho) ----------------
# A short human-style briefing built ONLY by rules over fields the robot
# actually collected — no LLM, no invented numbers. A fact the robot
# does not have (exact shipping fee, a shop it cannot place) is left
# out, never guessed.

# Substrings found in Up Garage shop names → (PT label, in Kanto?).
# Kanto = the prefectures Fabricio can realistically drive to from Gyoda.
PLACES = [
    ("札幌", "Sapporo", False), ("仙台", "Sendai", False),
    ("横浜", "Yokohama", True), ("川崎", "Kawasaki", True),
    ("名古屋", "Nagoya", False), ("神戸", "Kobe", False),
    ("北海道", "Hokkaido", False), ("青森", "Aomori", False),
    ("岩手", "Iwate", False), ("宮城", "Miyagi", False),
    ("秋田", "Akita", False), ("山形", "Yamagata", False),
    ("福島", "Fukushima", False), ("茨城", "Ibaraki", True),
    ("栃木", "Tochigi", True), ("群馬", "Gunma", True),
    ("埼玉", "Saitama", True), ("千葉", "Chiba", True),
    ("東京", "Tóquio", True), ("神奈川", "Kanagawa", True),
    ("新潟", "Niigata", False), ("富山", "Toyama", False),
    ("石川", "Ishikawa", False), ("福井", "Fukui", False),
    ("山梨", "Yamanashi", False), ("長野", "Nagano", False),
    ("岐阜", "Gifu", False), ("静岡", "Shizuoka", False),
    ("愛知", "Aichi", False), ("三重", "Mie", False),
    ("滋賀", "Shiga", False), ("京都", "Kyoto", False),
    ("大阪", "Osaka", False), ("兵庫", "Hyogo", False),
    ("奈良", "Nara", False), ("和歌山", "Wakayama", False),
    ("鳥取", "Tottori", False), ("島根", "Shimane", False),
    ("岡山", "Okayama", False), ("広島", "Hiroshima", False),
    ("山口", "Yamaguchi", False), ("徳島", "Tokushima", False),
    ("香川", "Kagawa", False), ("愛媛", "Ehime", False),
    ("高知", "Kochi", False), ("福岡", "Fukuoka", False),
    ("佐賀", "Saga", False), ("長崎", "Nagasaki", False),
    ("熊本", "Kumamoto", False), ("大分", "Oita", False),
    ("宮崎", "Miyazaki", False), ("鹿児島", "Kagoshima", False),
    ("沖縄", "Okinawa", False),
]


def place_of(item):
    """(label, in_kanto) from the shop name — None when the robot cannot
    place the shop, in which case the verdict says nothing about distance."""
    shop = item.get("shop") or ""
    for jp, label, kanto in PLACES:
        if jp in shop:
            return label, kanto
    return None


def short_title(title, n=40):
    title = (title or "").strip()
    return title if len(title) <= n else title[:n] + "…"


def fmt_end(iso):
    """'2026-11-27T22:00:00+09:00' → '27/11 às 22:00' (None if unparsable)."""
    try:
        return datetime.fromisoformat(iso).strftime("%d/%m às %H:%M")
    except (TypeError, ValueError):
        return None


def yen_txt(price):
    return f"¥{price:,}" if price is not None else "preço no anúncio"


def is_complete_title(it):
    """Conservative title-only read: names a full system/base and does
    not admit to being the unit alone."""
    t = norm(it["title"])
    return (any(m in t for m in ("システムキャリア", "ベースキャリア"))
            and "本体のみ" not in t)


def is_complete_verified(it):
    """Verified from the seller's own description (Up Garage detail):
    NOT unit-only, and the kit enumerates keys AND mounting bolts."""
    return (it.get("unit_only") is False
            and bool(it.get("has_keys")) and bool(it.get("has_bolts")))


def build_verdict(want, profile, fits, near, examples):
    """The resuminho: 0–5 short PT lines. Every number comes from the
    items themselves. Lines whose facts are missing are omitted."""
    ceiling = want.get("ceiling")
    lines = []
    best = fits[0] if fits else None

    # ---- headline ----
    if best is not None:
        virtues = ["encaixe confirmado" if profile else "confere com a procura"]
        if (ceiling is not None and best["price"] is not None
                and best["price"] < ceiling):
            virtues.append(f"¥{ceiling - best['price']:,} abaixo do teto")
        place = place_of(best)
        if place:
            virtues.append(f"loja em {place[0]}")
        head = (f"O achado: {short_title(best['title'], 42)} por "
                f"{yen_txt(best['price'])} — " + ", ".join(virtues))
        caveats = []
        if best["kind"] == "auction":
            if best.get("buyout"):
                c = f"é leilão — compra imediata por ¥{best['buyout']:,}"
            else:
                c = "é leilão — o preço mostrado é o lance atual"
            end = fmt_end(best.get("end_time"))
            if end:
                c += f", termina {end}"
            caveats.append(c)
        if best.get("unit_only"):
            caveats.append("é só o corpo (本体のみ) — sem chaves/parafusos "
                           "listados no anúncio")
        head += ". Mas " + "; ".join(caveats) + "." if caveats else "."
        lines.append(head)
    elif near:
        top = near[0]
        line = (f"Nada fechado hoje: o mais perto é "
                f"{short_title(top['title'], 42)} por {yen_txt(top['price'])}")
        if top.get("over"):
            line += f" (+¥{top['over']:,} do teto)"
        lines.append(line + ".")
    else:
        lines.append("Nada fechado hoje — e nada nem perto do teto "
                     "nesta varredura.")

    # ---- attention: cheapest candidate carrying a catch ----
    def catches(it):
        out = []
        if it["kind"] == "auction":
            end = fmt_end(it.get("end_time"))
            out.append("é leilão" + (f" (termina {end})" if end else ""))
        if it.get("unit_only"):
            out.append("é só o corpo (本体のみ)")
        place = place_of(it)
        if place and not place[1]:
            out.append(f"loja longe, em {place[0]} — some o frete "
                       "antes de comparar")
        if (it.get("unit_only") is False and it.get("has_keys")
                and not it.get("has_bolts")):
            out.append("o anúncio lista corpo e chaves, mas não os "
                       "parafusos de fixação")
        return out

    cands = []
    for it in fits[1:] + near:
        if it["price"] is None:
            continue
        c = catches(it)
        if c:
            cands.append((it["price"], it, c))
    cands.sort(key=lambda x: x[0])
    if cands:
        _, trap, c = cands[0]
        lines.append(f"Cuidado: {short_title(trap['title'])} por "
                     f"¥{trap['price']:,} — " + "; ".join(c) + ".")

    # ---- price ruler: cheapest honestly-complete near-miss ----
    ruler = None
    if profile and near:
        priced = [it for it in near if it["price"] is not None]
        pool = ([it for it in priced if is_complete_verified(it)]
                or [it for it in priced if is_complete_title(it)])
        if pool:
            ruler = min(pool, key=lambda x: x["price"])
    if ruler is not None:
        line = (f"Conjunto completo de verdade começa em "
                f"¥{ruler['price']:,} ({ruler['source']})")
        if is_complete_verified(ruler):
            line += " — com chaves e parafusos listados no anúncio"
        place = place_of(ruler)
        if place and not place[1]:
            line += (f"; mas a loja é em {place[0]}, longe — some o "
                     "frete antes de comparar")
        lines.append(line + ".")

    # ---- missing piece: base bought, snowboard attachment still needed ----
    if profile and best is not None and examples:
        t = norm(best["title"])
        is_base = any(m in t for m in ("システムキャリア", "ベースキャリア",
                                       "ルーフキャリア"))
        has_attach = any(m in t for m in profile["attach_markers"])
        attach_ex = [e for e in examples
                     if "acessório de prancha" in (e.get("reason") or "")
                     and e["price"] is not None]
        if is_base and not has_attach and attach_ex:
            e = min(attach_ex, key=lambda x: x["price"])
            lines.append(f"Falta o acessório de prancha — ele aparece por "
                         f"~¥{e['price']:,} ({e['source']}); monta em "
                         "cima dessa base.")
    return lines[:5]


# ---------------- main ----------------

def hunt(want):
    what = want["what"]
    details = want.get("details") or ""
    ceiling = want.get("ceiling")
    queries = [what] + ([details] if details else [])
    what_toks = tokens_of(what)
    phrase = norm(what)
    profile = fitment_profile_for(want)
    if profile:
        for q in profile["queries"]:
            if q not in queries:
                queries.append(q)
        log(f"fitment profile active: {profile['car_label']} "
            f"(sweep queries: {len(queries)})")

    all_items, source_status = [], []
    for name, fn in SOURCES:
        try:
            got = fn(queries)
            source_status.append({"name": name, "status": "ok", "found": len(got)})
            all_items.extend(got)
            log(f"{name}: {len(got)} listings swept")
        except Exception as e:  # one source failing never kills the run
            source_status.append({"name": name, "status": f"error: {type(e).__name__}",
                                  "found": 0})
            log(f"{name}: FAILED {type(e).__name__}: {e}")
        time.sleep(SLEEP_BETWEEN)

    swept = len(all_items)
    fits, near, unconfirmed, examples = [], [], [], []
    rejected, seen_urls = 0, set()
    for it in all_items:
        if it["url"] in seen_urls:
            rejected += 1
            continue
        seen_urls.add(it["url"])
        t = norm(it["title"])
        if profile:
            tier, reason, prio = classify_with_profile(it, t, profile, ceiling)
        else:
            tier, reason, prio = classify_generic(it, t, what_toks, phrase, ceiling)
        if tier == "fit":
            fits.append(it)
            continue
        rejected += 1  # everything not a confirmed fit counts as discarded
        if tier == "reject":
            continue
        entry = dict(it)
        entry["reason"] = reason
        if tier == "near":
            if ceiling is not None and it["price"] is not None:
                entry["over"] = it["price"] - ceiling
            near.append(entry)
        elif tier == "unconfirmed":
            unconfirmed.append(entry)
        else:
            entry["_prio"] = prio
            examples.append(entry)

    by_price = lambda x: (x["price"] is None,
                          x["price"] if x["price"] is not None else 0)
    fits.sort(key=by_price)
    near.sort(key=by_price)
    unconfirmed.sort(key=by_price)
    # examples: attachment-only first (the trap Fabricio named), then
    # other-model, then part-only — cheapest first inside each family
    examples.sort(key=lambda x: (x["_prio"], by_price(x)))
    near_total, unconfirmed_total = len(near), len(unconfirmed)
    near, unconfirmed, examples = near[:5], unconfirmed[:3], examples[:2]
    for e in examples:
        e.pop("_prio", None)

    # Enrich the SHOWN Up Garage items with their detail records (shop,
    # auction truth, 本体のみ, parts) — the verdict rules read these.
    for it in fits[:10] + near + unconfirmed + examples:
        if it["source"] == "Up Garage":
            enrich_upgarage(it)
    verdict = build_verdict(want, profile, fits, near, examples)

    notes = []
    ok_sources = [s["name"] for s in source_status if s["status"] == "ok"]
    bad_sources = [s["name"] for s in source_status if s["status"] != "ok"]
    if bad_sources:
        notes.append("Fontes que não responderam nesta varredura: " + ", ".join(bad_sources) +
                     ". O robô tenta de novo na próxima.")
    if any(f["kind"] == "auction" and f["source"] == "Yahoo! Auctions"
           for f in fits + near + unconfirmed):
        notes.append("Itens do Yahoo! Auctions mostram o lance atual — o preço pode subir "
                     "até o fim do leilão.")
    if any(f["kind"] == "auction" and f["source"] == "Up Garage"
           for f in fits + near + unconfirmed):
        notes.append("No Up Garage, item marcado como leilão tem a data de término no "
                     "anúncio — e o preço exibido é o da compra imediata, quando ela existe.")
    if ceiling is not None:
        cheap = [f for f in fits if f["price"] is not None and f["price"] <= ceiling * 0.4]
        if cheap:
            notes.append(f"{len(cheap)} achado(s) muito abaixo do teto (≤40%): confira estado, "
                         "fotos e vendedor antes de fechar — preço baixo demais também é sinal.")
    if not fits and near:
        top = near[0]
        title = top["title"]
        if len(title) > 48:
            title = title[:48] + "…"
        notes.append(f"O mais perto: {title} por ¥{top['price']:,} — "
                     f"¥{top['over']:,} acima do teto.")
    if unconfirmed:
        car = profile["car_label"] if profile else "carro"
        notes.append(f"{len(unconfirmed)} anúncio(s) do tipo certo, mas o título não "
                     f"confirma o encaixe na {car} — estão no QUASE pra você conferir.")
    if not fits and not near:
        notes.append("Nada dentro do teto e das especificações por enquanto — a procura "
                     "continua viva e o robô segue vigiando.")

    results = {
        "want_number": want.get("number"),
        "want_what": what,
        "swept_at": datetime.now(JST).isoformat(timespec="seconds"),
        "fits": fits[:30],
        "fits_total": len(fits),
        "near": near,
        "near_total": near_total,
        "unconfirmed": unconfirmed,
        "unconfirmed_total": unconfirmed_total,
        "examples": examples,
        "swept": swept,
        "rejected": rejected,
        "sources": source_status,
        "notes": notes,
        "verdict": verdict,
    }
    log(f"delivery ready: {len(fits)} fits / {near_total} near / "
        f"{unconfirmed_total} unconfirmed / {len(examples)} examples / "
        f"{swept} swept / {rejected} rejected "
        f"(sources ok: {', '.join(ok_sources)})")
    return results


def main():
    wants = []
    if WANTS_FILE.exists():
        wants = json.loads(WANTS_FILE.read_text(encoding="utf-8"))
    elif WANT_FILE.exists():
        wants = [json.loads(WANT_FILE.read_text(encoding="utf-8"))]
    active = [w for w in wants if w.get("active") and w.get("what")]
    if not active:
        log("no active wants — robot idle")
        return 0
    board_want, board_results = None, None
    for want in active:
        log(f"=== QUERO Nº {want.get('number')}: {want.get('what')} ===")
        results = hunt(want)
        out = BASE / f"results-{want.get('number')}.json"
        out.write_text(json.dumps(results, ensure_ascii=False, indent=1),
                       encoding="utf-8")
        board_want, board_results = want, results
    board = {"want": board_want, "results": board_results, "wants": wants}
    BOARD_FILE.write_text(json.dumps(board, ensure_ascii=False, indent=1),
                          encoding="utf-8")
    log(f"board updated for QUERO Nº {board_want.get('number')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
