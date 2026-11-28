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
import json, os, re, sys, time, urllib.error, urllib.parse, urllib.request
from datetime import datetime, timezone, timedelta
from html import unescape
from pathlib import Path

BASE = Path(__file__).resolve().parent
WANT_FILE = BASE / "want.json"
RESULTS_FILE = BASE / "results.json"
WANTS_FILE = BASE / "wants.json"
BOARD_FILE = BASE / "board.json"
LOG_FILE = BASE / "hunter.log"
FACTS_FILE = BASE / "facts.json"
GEMINI_KEY = os.environ.get("GEMINI_API_KEY", "")
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.8-flash")
GROQ_KEY = os.environ.get("GROQ_API_KEY", "")
GROQ_MODEL = os.environ.get("GROQ_MODEL", "openai/gpt-oss-120b")

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


JINA_KEY = os.environ.get("JINA_API_KEY", "")


def fetch_via_jina(url):
    """Jina Reader rescue: the page's clean text, rendered by Jina
    (JavaScript and all, PDFs too) via r.jina.ai. Keyless works
    (20 reads/min per IP); a JINA_API_KEY secret raises the ceiling
    whenever one exists — no code change needed."""
    headers = {"User-Agent": UA, "Accept": "text/plain"}
    if JINA_KEY:
        headers["Authorization"] = "Bearer " + JINA_KEY
    req = urllib.request.Request("https://r.jina.ai/" + url,
                                 headers=headers)
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read().decode("utf-8", "replace")


def rescue_text(url, direct_text):
    """If the direct read came back thin, let Jina try; keep the
    longer text. Returns the winning text (may be the direct one)."""
    if len(direct_text) >= 200:
        return direct_text
    try:
        jt = fetch_via_jina(url)
        if len(jt) > len(direct_text):
            log(f"fact read via jina: {url}")
            return jt
    except Exception:
        pass
    return direct_text


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
    """Mercari — the search page is a JS app. Three harvest paths, in
    order of trust: (1) JSON responses intercepted in flight,
    (2) the page's embedded __NEXT_DATA__ JSON (prices in JPY),
    (3) the rendered DOM cards. A DOM price rendered in a foreign
    currency by the datacenter's locale is NEVER converted or
    guessed — the card is kept with price=None (title + URL still
    useful; the fit engine already tolerates None, as with Rakuten).
    Raises with diagnostics when nothing is captured — the run
    tolerates a failed source by design."""
    from playwright.sync_api import sync_playwright
    items, seen = [], set()
    diag = {"responses": 0, "next_data": 0, "anchors": 0}

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
                if "mercari" not in resp.url or resp.status != 200:
                    return
                ct = (resp.headers or {}).get("content-type", "")
                if ("json" not in ct and "api" not in resp.url
                        and "_next/data" not in resp.url):
                    return
                captured.append(resp.json())
                diag["responses"] += 1
            except Exception:
                pass

        pg.on("response", on_response)
        for q in queries[:2]:
            url = ("https://jp.mercari.com/search?keyword="
                   + urllib.parse.quote(q))
            pg.goto(url, wait_until="domcontentloaded", timeout=60000)
            try:
                pg.wait_for_selector('a[href*="/item/"]', timeout=25000)
            except Exception:
                pass
            pg.wait_for_timeout(3000)
            for data in captured:
                harvest(data)
            captured.clear()
            if not items:
                try:
                    nd = pg.evaluate(
                        "() => { const el = document.getElementById("
                        "'__NEXT_DATA__'); "
                        "return el ? el.textContent : null; }")
                    if nd:
                        diag["next_data"] += 1
                        harvest(json.loads(nd))
                except Exception:
                    pass
            if not items:
                anchors = pg.query_selector_all('a[href*="/item/"]')
                diag["anchors"] += len(anchors)
                for a in anchors:
                    href = a.get_attribute("href") or ""
                    m = re.search(r"/item/(m\w+)", href)
                    if not m or m.group(1) in seen:
                        continue
                    txt = re.sub(r"\s+", " ",
                                 (a.inner_text() or "")).strip()
                    pm = re.search(r"¥\s*([\d,]+)", txt)
                    if pm:
                        title = (txt[pm.end():].strip(" 　")
                                 or txt[:pm.start()].strip())
                        price = int(pm.group(1).replace(",", ""))
                    elif re.search(r"\$\s*[\d,]+", txt):
                        title = re.sub(r"\$\s*[\d,]+\s*", "", txt).strip()
                        price = None
                    else:
                        continue
                    if not title:
                        continue
                    seen.add(m.group(1))
                    items.append({
                        "title": title,
                        "price": price,
                        "url": "https://jp.mercari.com/item/" + m.group(1),
                        "image": None,
                        "source": "Mercari",
                        "kind": "classified",
                    })
            time.sleep(SLEEP_BETWEEN)
        b.close()
    if not items:
        raise RuntimeError(
            "no Mercari items captured "
            f"(responses={diag['responses']}, "
            f"next_data={diag['next_data']}, anchors={diag['anchors']})")
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


# ---------------- the eye (fact hunts) ----------------
# The eye reads official pages and answers ONLY what the page says.
# The algorithm leashes it: a verdict without a verbatim quote found
# in the fetched page text is downgraded to "nao_diz". AI perceives,
# the algorithm decides — the eye never invents.

AGGREGATOR_HOSTS = (
    "jalan.net", "rakuten.co.jp", "tripadvisor", "jtb.co.jp",
    "booking.com", "expedia", "hotels.com", "ikyu.com", "agoda",
    "trivago", "relux.jp", "rurubu", "nifty.com", "yahoo.co.jp", "google.",
    "amazon.", "trip.com", "kkday", "klook",
)


def html_to_text(html):
    h = re.sub(r"(?is)<(script|style|noscript)[^>]*>.*?</\\1>", " ", html or "")
    h = re.sub(r"(?s)<[^>]+>", " ", h)
    return re.sub(r"\\s+", " ", unescape(h)).strip()


def gemini_json(prompt):
    if not GEMINI_KEY:
        raise RuntimeError("GEMINI_API_KEY missing — the eye is off")
    url = ("https://generativelanguage.googleapis.com/v1beta/models/"
           + GEMINI_MODEL + ":generateContent")
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.1,
                             "responseMimeType": "application/json"},
    }
    req = urllib.request.Request(
        url, data=json.dumps(payload).encode("utf-8"), method="POST",
        headers={"Content-Type": "application/json",
                 "User-Agent": UA,
                 "x-goog-api-key": GEMINI_KEY})
    with urllib.request.urlopen(req, timeout=120) as r:
        data = json.loads(r.read().decode("utf-8", "replace"))
    text = data["candidates"][0]["content"]["parts"][0]["text"]
    return json.loads(text)


def groq_json(prompt):
    if not GROQ_KEY:
        raise RuntimeError("GROQ_API_KEY missing — the Groq lens is off")
    payload = {
        "model": GROQ_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.1,
        "response_format": {"type": "json_object"},
    }
    req = urllib.request.Request(
        "https://api.groq.com/openai/v1/chat/completions",
        data=json.dumps(payload).encode("utf-8"), method="POST",
        headers={"Content-Type": "application/json",
                 "User-Agent": UA,
                 "Authorization": "Bearer " + GROQ_KEY})
    with urllib.request.urlopen(req, timeout=120) as r:
        data = json.loads(r.read().decode("utf-8", "replace"))
    text = (data["choices"][0]["message"]["content"] or "").strip()
    if text.startswith("```"):
        text = re.sub(r"^```[a-z]*\s*|\s*```$", "", text).strip()
    return json.loads(text)


_EYE_DOWN = set()
_EYE_LAST = {"provider": "groq"}
EYE_ERRORS = {}
_EYE_REST_UNTIL = {}
_EYE_STRIKES = {}


def _is_limit_error(e):
    if getattr(e, "code", None) == 429:
        return True
    s = str(e)
    return "429" in s or "rate_limit" in s or "RESOURCE_EXHAUSTED" in s


def _err_detail(e):
    """Short, safe description of a provider error for the delivery:
    type + HTTP code + a slice of the API's own message (never a key)."""
    code = getattr(e, "code", None)
    body = ""
    if code is not None:
        try:
            body = e.read().decode("utf-8", "replace")[:220]
        except Exception:
            body = ""
    if not body:
        body = str(e)[:220]
    return f"{type(e).__name__} code={code}: {body}".strip()


def eye_json(prompt):
    """The eye, with two lenses (Fabricio's call, 2026-11-25): Groq
    reads first; when its free quota ends, Gemini takes over. A lens
    that hits its PER-MINUTE free limit rests (65s, then 5 min) and
    comes back — the other lens keeps working meanwhile. Only a
    lens that hits the limit 3 times sits out the rest of the run.
    The queue never stops."""
    providers = []
    if GROQ_KEY:
        providers.append(("groq", groq_json))
    if GEMINI_KEY:
        providers.append(("gemini", gemini_json))
    if not providers:
        raise RuntimeError(
            "no eye key (GROQ_API_KEY/GEMINI_API_KEY) — the eye is off")
    last_err = None
    for _pass in range(2):
        for name, fn in providers:
            if name in _EYE_DOWN:
                continue
            if time.time() < _EYE_REST_UNTIL.get(name, 0):
                continue
            for attempt in (1, 2):
                try:
                    out = fn(prompt)
                    _EYE_LAST["provider"] = name
                    return out
                except Exception as e:
                    last_err = e
                    code = getattr(e, "code", None)
                    is_timeout = isinstance(e, TimeoutError)
                    if attempt == 1 and (code in (500, 502, 503, 504)
                                         or is_timeout):
                        wait = 10 if is_timeout else 20
                        why = ("timed out" if is_timeout
                               else f"answered {code}")
                        log(f"eye: {name} {why} (transient) — "
                            f"waiting {wait}s, retrying this lens")
                        time.sleep(wait)
                        continue
                    if _is_limit_error(e):
                        _EYE_STRIKES[name] = _EYE_STRIKES.get(name, 0) + 1
                        if _EYE_STRIKES[name] >= 3:
                            _EYE_DOWN.add(name)
                            log(f"eye: {name} hit its free limit 3x — "
                                "sitting out this run")
                        else:
                            rest = 65 if _EYE_STRIKES[name] == 1 else 300
                            _EYE_REST_UNTIL[name] = time.time() + rest
                            log(f"eye: {name} hit its free limit — "
                                f"resting {rest}s, other lens keeps going")
                    else:
                        EYE_ERRORS[name] = _err_detail(e)
                        log(f"eye: {name} failed ({type(e).__name__}) "
                            "— trying the other lens")
                    break
        if _pass == 0:
            resting = [t for n, t in _EYE_REST_UNTIL.items()
                       if n not in _EYE_DOWN and t > time.time()]
            if resting:
                wait = min(resting) - time.time() + 2
                if wait <= 320:
                    log(f"eye: all lenses resting — waiting {int(wait)}s")
                    time.sleep(wait)
                    continue
        break
    if last_err is not None:
        raise last_err
    raise RuntimeError("both eye lenses are resting")


def eye_pace():
    """Free-tier pace between eye calls: Groq is fast (3s is gentle);
    Gemini free is ~5 calls/minute, so 13s when Gemini served last."""
    time.sleep(13 if _EYE_LAST["provider"] == "gemini" else 3)


def eye_plan(want):
    """One eye call: turn the PT want into JP searches + criteria."""
    prompt = (
        "Você é o planejador de buscas do Karutaro. O usuário procura um "
        "FATO ou LUGAR, não um produto.\n"
        f"Procura: \"{want.get('what')}\"\n"
        f"Detalhes/critérios: \"{want.get('details') or ''}\"\n"
        "Responda SOMENTE um JSON assim: "
        '{"queries": ["...","...","..."], "criteria": '
        '[{"id":"...","label":"...","ask_jp":"..."}]}\n'
        "- queries: 3 buscas em JAPONÊS para achar as páginas OFICIAIS dos "
        "lugares (inclua a palavra 公式 em pelo menos duas). Uma das "
        "buscas deve mirar a página de REGRAS do lugar — inclua nela "
        "よくある質問 ou 利用案内.\n"
        "- criteria: UMA pergunta por critério citado nos detalhes. "
        "id = palavra curta sem espaços; label = a pergunta em português, "
        "curta (ex.: \"Pode tatuagem?\"); ask_jp = a mesma pergunta em "
        "japonês; keywords = 2 a 4 palavras japonesas que a página usaria ao tratar do assunto (ex.: para tatuagem: タトゥー, 刺青, 入れ墨). Se os detalhes não citarem critério, crie um critério "
        "único a partir da procura."
    )
    plan = eye_json(prompt)
    queries = [q for q in plan.get("queries", []) if q][:3]
    criteria = []
    for c in plan.get("criteria", [])[:4]:
        if c.get("id") and c.get("ask_jp"):
            criteria.append({"id": str(c["id"]),
                             "label": str(c.get("label") or c["id"]),
                             "ask_jp": str(c["ask_jp"]),
                             "keywords": [str(k) for k in (c.get("keywords") or [])][:4]})
    if not queries:
        queries = [(want.get("what") or "") + " 公式"]
    if not criteria:
        criteria = [{"id": "geral", "label": want.get("details") or "Confere?",
                     "ask_jp": want.get("what") or ""}]
    return queries, criteria


def _parse_ddg(html, limit):
    out, seen = [], set()
    for m in re.finditer(r'href="([^"]+)"[^>]*>([^<]{2,120})</a>', html):
        href, title = m.group(1), unescape(m.group(2)).strip()
        um = re.search(r"[?&]uddg=([^&]+)", href)
        if um:
            href = urllib.parse.unquote(um.group(1))
        if not href.startswith("http") or href in seen:
            continue
        if "duckduckgo.com" in href:
            continue
        seen.add(href)
        out.append({"title": title, "url": href})
        if len(out) >= limit:
            break
    return out


def _parse_yahoo(html, limit):
    """Yahoo! Japan search: result titles are direct links
    (class sw-Card__titleInner) — no redirect wrapper."""
    out, seen = [], set()
    for m in re.finditer(
            r'<a href="([^"]+)" class="sw-Card__titleInner"[^>]*>(.*?)</a>',
            html, re.S):
        href = unescape(m.group(1))
        title = unescape(re.sub(r"<[^>]+>", "", m.group(2))).strip()
        if not href.startswith("http") or href in seen:
            continue
        seen.add(href)
        out.append({"title": title, "url": href})
        if len(out) >= limit:
            break
    return out


def web_search(query, limit=10):
    """Search for the fact hunt — no key needed. DuckDuckGo first;
    from GitHub's runners DDG answers empty (IP reputation), so
    Yahoo! Japan is the second engine. Returns [{title, url}]."""
    engines = (
        ("ddg", "https://html.duckduckgo.com/html/?q=", _parse_ddg),
        ("ddg-lite", "https://lite.duckduckgo.com/lite/?q=", _parse_ddg),
        ("yahoo", "https://search.yahoo.co.jp/search?p=", _parse_yahoo),
    )
    for name, base, parse in engines:
        try:
            page = fetch(base + urllib.parse.quote(query))
            out = parse(page, limit)
        except Exception as e:
            log(f"web search failed ({name}): {type(e).__name__}")
            continue
        log(f"web search ({name}): {len(out)} results")
        if out:
            return out
    return []


def _squash(s):
    return re.sub(r"\\s+", "", (s or "")).lower()


def _excerpts(text, criteria, budget=11000):
    """Ctrl+F reading: instead of the page's first N chars, cut
    windows around the criteria's keywords — the rules live deep
    in long pages (Tonbo no Yu's tattoo rule sits at char 29,690
    of 39,785; a head-only read never reaches it)."""
    words = []
    for c in criteria:
        for k in c.get("keywords") or []:
            if k and k not in words:
                words.append(k)
    if not words or not text:
        return text[:6000]
    spans = []
    for w in words:
        start = 0
        for _ in range(3):
            i = text.find(w, start)
            if i < 0:
                break
            spans.append((max(0, i - 700),
                          min(len(text), i + len(w) + 700)))
            start = i + len(w)
    if not spans:
        return text[:6000]
    spans.sort()
    merged = [list(spans[0])]
    for a, b in spans[1:]:
        if a <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], b)
        else:
            merged.append([a, b])
    out, total = [], 0
    for a, b in merged:
        seg = text[a:b]
        if total + len(seg) > budget:
            seg = seg[:budget - total]
        if seg:
            out.append(seg)
            total += len(seg)
        if total >= budget:
            break
    return "\n…\n".join(out)


def eye_read_page(url, page_text, criteria):
    qs = "\n".join(f"- id \"{c['id']}\": {c['ask_jp']}" for c in criteria)
    prompt = (
        "Você é o OLHO do Karutaro. Leia o texto da página abaixo e "
        "responda às perguntas SOMENTE com o que a página diz. Nunca "
        "invente: se a página não disser, verdict = \"nao_diz\" e "
        "quote = \"\".\n"
        f"Perguntas:\n{qs}\n"
        "Responda SOMENTE um JSON: {\"place_name\": \"nome do lugar "
        "dono desta página\", \"answers\": [{\"id\": \"...\", "
        "\"verdict\": \"sim|nao|nao_diz\", \"quote\": \"trecho EXATO "
        "copiado da página que justifica a resposta (vazio se nao_diz)\"}]}\n"
        f"TEXTO DA PÁGINA:\n{page_text[:12000]}"
    )
    got = eye_json(prompt)
    answers = {}
    for a in got.get("answers", []):
        v = a.get("verdict")
        if v not in ("sim", "nao", "nao_diz"):
            v = "nao_diz"
        answers[a.get("id")] = {"verdict": v, "quote": (a.get("quote") or "").strip()}
    # THE LEASH: no verbatim quote in the page, no verdict.
    squashed = _squash(page_text)
    out = []
    for c in criteria:
        a = answers.get(c["id"], {"verdict": "nao_diz", "quote": ""})
        if a["verdict"] != "nao_diz":
            if not a["quote"] or _squash(a["quote"]) not in squashed:
                a = {"verdict": "nao_diz", "quote": ""}
        out.append({"criterion": c["id"], "label": c["label"],
                    "verdict": a["verdict"], "quote": a["quote"]})
    return (got.get("place_name") or "").strip(), out


RULE_LINK_WORDS = ("よくある質問", "faq", "ご利用案内", "利用案内",
                   "ご利用について", "入浴", "注意事項", "お願い",
                   "ルール", "規則", "施設案内", "営業案内",
                   "annai", "guide", "rules")


def follow_rule_links(page_url, page_html, cache):
    """Teach the feet: from a site's front page, follow up to 2
    same-host links that smell like rules (FAQ / usage guide) and
    bring their text back — that is where tattoo/children rules
    live, never on the front page. Returns (text, [urls])."""
    host = urllib.parse.urlparse(page_url).netloc.lower()
    found = []
    for m in re.finditer(r'<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>',
                         page_html, re.S | re.I):
        href = unescape(m.group(1)).strip()
        label = unescape(re.sub(r"<[^>]+>", "", m.group(2))).strip().lower()
        if not href or href.startswith(("#", "javascript:", "mailto:",
                                         "tel:")):
            continue
        full = urllib.parse.urljoin(page_url, href)
        p = urllib.parse.urlparse(full)
        if p.netloc.lower() != host:
            continue
        hay = label + " " + p.path.lower()
        if any(w in hay for w in RULE_LINK_WORDS):
            clean = full.split("#")[0]
            if clean != page_url.split("#")[0] and clean not in found:
                found.append(clean)
        if len(found) >= 2:
            break
    def _score(u):
        p = urllib.parse.urlparse(u).path.lower()
        s = 0
        if "faq" in p:
            s += 3
        if "day-use" in p or "%e6%97%a5%e5%b8%b0" in p:
            s += 3
        if "annai" in p:
            s += 2
        return s
    found.sort(key=_score, reverse=True)
    texts = []
    for u in found:
        if u not in cache:
            t = ""
            try:
                t = html_to_text(fetch(u))
            except Exception as e:
                log(f"fact nav failed {u}: {type(e).__name__}")
            cache[u] = rescue_text(u, t)
        if cache[u]:
            texts.append(cache[u][:4500])
    return "\n\n".join(texts), found


def hunt_fact(want):
    """Fact/place hunt: search official pages, read them with the eye,
    verify every quote, deliver per-place verdicts + the library."""
    now = datetime.now(JST).isoformat(timespec="seconds")
    base = {
        "kind": "fato", "want_number": want.get("number"),
        "want_what": want.get("what"), "swept_at": now,
        "fits": [], "fits_total": 0, "near": [], "near_total": 0,
        "unconfirmed": [], "unconfirmed_total": 0, "examples": [],
        "swept": 0, "rejected": 0, "notes": [], "sources": [],
    }
    prev_file = BASE / f"results-{want.get('number')}.json"
    if prev_file.exists():
        try:
            prev = json.loads(prev_file.read_text(encoding="utf-8"))
            age_h = (datetime.now(JST) - datetime.fromisoformat(
                prev["swept_at"])).total_seconds() / 3600
            if prev.get("kind") == "fato" and prev.get("eye") == "on" and age_h < 20:
                log(f"fact delivery still fresh ({age_h:.1f}h) — "
                    "facts change slowly; skipping the re-read")
                return prev
        except Exception:
            pass
    if not (GROQ_KEY or GEMINI_KEY):
        base["eye"] = "off"
        base["verdict"] = ["O olho ainda não foi ligado — faltam as "
                           "chaves do olho (Groq/Gemini) no cofre "
                           "do GitHub."]
        base["criteria"], base["places"] = [], []
        base["answered"] = 0
        log("fact hunt skipped: eye off (no eye keys)")
        return base
    base["eye"] = "on"
    try:
        queries, criteria = eye_plan(want)
    except Exception as e:
        log(f"eye plan failed: {type(e).__name__}: {e}")
        base["eye_error"] = _err_detail(e)
        if getattr(e, "code", None) == 429:
            base["verdict"] = ["A cota grátis do olho acabou por hoje — "
                               "ele tenta de novo amanhã."]
        else:
            base["verdict"] = ["O olho piscou na hora de planejar a busca — "
                               "tenta de novo na próxima varredura."]
        base["criteria"], base["places"] = [], []
        base["answered"] = 0
        base["eye_errors"] = dict(EYE_ERRORS)
        return base
    base["criteria"] = [{"id": c["id"], "label": c["label"]} for c in criteria]
    log(f"eye plan: {len(queries)} queries, {len(criteria)} criteria")
    log(f"fact queries: {queries}")

    candidates, seen_hosts, skipped = [], set(), 0
    for q in queries:
        for r in web_search(q):
            host = urllib.parse.urlparse(r["url"]).netloc.lower()
            if any(a in host for a in AGGREGATOR_HOSTS):
                skipped += 1
                continue
            if host in seen_hosts:
                continue
            seen_hosts.add(host)
            candidates.append(r)
        time.sleep(SLEEP_BETWEEN)
    candidates = candidates[:6]
    log(f"fact candidates: {len(candidates)} official pages "
        f"({skipped} aggregator results skipped)")

    places = []
    eye_pace()  # free-tier pace before the first read
    nav_cache = {}
    for cand in candidates:
        try:
            page_html = ""
            text = ""
            try:
                page_html = fetch(cand["url"])
                text = html_to_text(page_html)
            except Exception as e:
                log(f"fact fetch failed {cand['url']}: {type(e).__name__}")
            if len(text) < 200:
                text = rescue_text(cand["url"], text)
                if len(text) >= 200:
                    page_html = ""  # Jina text: no HTML links to follow
            if len(text) < 200:
                log(f"fact page too short ({len(text)} chars): {cand['url']}")
                continue
            nav_text, nav_urls = follow_rule_links(cand["url"], page_html,
                                                   nav_cache)
            if nav_urls:
                log(f"fact nav: {cand['url']} -> {nav_urls}")
            full_text = (nav_text + "\n\n" + text) if nav_text else text
            read_text = _excerpts(full_text, criteria)
            name, answers = eye_read_page(cand["url"], read_text, criteria)
            places.append({
                "name": name or cand["title"], "url": cand["url"],
                "domain": urllib.parse.urlparse(cand["url"]).netloc,
                "answers": answers, "read_at": now,
                "read_pages": [cand["url"]] + nav_urls,
            })
            log(f"eye read: {name or cand['url']} "
                f"({sum(1 for a in answers if a['verdict'] != 'nao_diz')} answered)")
        except Exception as e:
            log(f"eye read failed {cand['url']}: {type(e).__name__}: {e}")
            if "eye_error" not in base:
                base["eye_error"] = _err_detail(e)
        eye_pace()  # free-tier pace between eye calls

    answered_places = [p for p in places
                       if any(a["verdict"] != "nao_diz" for a in p["answers"])]
    full = [p for p in places
            if all(a["verdict"] == "sim" for a in p["answers"])]
    base["places"] = places
    base["answered"] = len(answered_places)
    base["fits_total"] = len(answered_places)
    base["swept"] = len(places)
    base["sources"] = [{"name": "Páginas oficiais (olho)",
                        "status": "ok", "found": len(places)}]
    if skipped:
        base["notes"].append(
            f"{skipped} resultado(s) de agregadores (reservas/guias) foram "
            "ignorados — o olho lê a página oficial do lugar.")
    base["notes"].append(
        "Cada veredito só vale com o trecho da página ao lado — sem "
        "trecho, o Karutaro marca NÃO DIZ. Leitura de " +
        datetime.now(JST).strftime("%d/%m/%Y") + ".")
    vlabel = {"sim": "PODE", "nao": "NÃO PODE", "nao_diz": "NÃO DIZ"}
    verdict = []
    if full:
        verdict.append(f"Achei: 【{full[0]['name']}】 responde SIM pra tudo "
                       "que você perguntou.")
    elif answered_places:
        n, m = len(places), len(answered_places)
        verdict.append(f"Li {n} página{'s' if n != 1 else ''} "
                       f"oficia{'is' if n != 1 else 'l'} — {m} "
                       f"respondeu às suas perguntas." if m == 1 else
                       f"Li {n} páginas oficiais — {m} responderam às "
                       "suas perguntas.")
    else:
        verdict.append(f"Li {len(places)} páginas oficiais e nenhuma "
                       "respondeu às suas perguntas — sigo vigiando.")
    for p in answered_places[:3]:
        parts = " · ".join(f"{a['label'].replace('?', '')}: {vlabel[a['verdict']]}"
                           for a in p["answers"])
        verdict.append(f"【{p['name']}】 {parts}")
    base["verdict"] = verdict

    # the library: every place read stays on record, date-stamped
    try:
        facts = []
        if FACTS_FILE.exists():
            facts = json.loads(FACTS_FILE.read_text(encoding="utf-8"))
        by_url = {x["url"]: x for x in facts}
        for p in places:
            by_url[p["url"]] = {"name": p["name"], "url": p["url"],
                                "answers": p["answers"],
                                "read_at": p["read_at"],
                                "want_number": want.get("number")}
        FACTS_FILE.write_text(json.dumps(list(by_url.values()),
                                         ensure_ascii=False, indent=1),
                              encoding="utf-8")
    except Exception as e:
        log(f"facts library write failed: {type(e).__name__}")
    base["eye_errors"] = dict(EYE_ERRORS)
    log(f"fact delivery ready: {len(places)} places read, "
        f"{len(answered_places)} answered, {len(full)} full matches")
    return base


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
        results = hunt_fact(want) if want.get("kind") == "fato" else hunt(want)
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
