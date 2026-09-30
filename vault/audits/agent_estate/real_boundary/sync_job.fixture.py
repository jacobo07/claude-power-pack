import json
import urllib.request


def fetch_orders(url):
    try:
        with urllib.request.urlopen(url, timeout=5) as r:
            return json.load(r)
    except Exception:
        return []


def save(orders, path):
    try:
        with open(path, "w") as f:
            json.dump(orders, f)
    except OSError:
        pass


def run(url, path):
    orders = fetch_orders(url)
    save(orders, path)
    print("sync complete")
