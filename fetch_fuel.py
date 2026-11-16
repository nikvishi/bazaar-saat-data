#!/usr/bin/env python3
"""Build fuel.json (today + yesterday retail prices) from Goodreturns city/state tables.
Run once a day. Prices are reported figures, not an official feed."""
import html, json, re, sys, urllib.request
from datetime import datetime, timezone

SRC = "https://www.goodreturns.in/{}-price.html"
UA = "Mozilla/5.0 (compatible; bazaar-saat-data/1.0; daily, personal info app)"


def rows(fuel):
    req = urllib.request.Request(SRC.format(fuel), headers={"User-Agent": UA})
    page = urllib.request.urlopen(req, timeout=30).read().decode("utf-8", "ignore")
    page = re.sub(r"<script.*?</script>|<style.*?</style>", "", page, flags=re.S)
    out = {}
    for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", page, flags=re.S):
        c = [html.unescape(re.sub(r"<[^>]+>", "", x)).strip() for x in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", tr, flags=re.S)]
        if len(c) >= 3 and c[1].startswith("₹"):
            try:
                price = float(c[1].replace("₹", "").replace(",", "").strip())
                delta = float(c[2].replace("+", "").replace(",", "").strip() or 0)
            except ValueError:
                continue
            out[c[0]] = {"today": round(price, 2), "yesterday": round(price - delta, 2)}
    return out


def main():
    data = {}
    for fuel in ("petrol", "diesel", "cng"):
        r = rows(fuel)
        if len(r) < 20:
            sys.exit(f"{fuel}: only {len(r)} rows, page layout may have changed; keeping old file")
        data[fuel] = r
    doc = {
        "updated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%MZ"),
        "source": "Goodreturns city tables (reported prices, not official)",
        "prices": data,
    }
    with open("fuel.json", "w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False, indent=1)
    print({k: len(v) for k, v in data.items()})


main()
