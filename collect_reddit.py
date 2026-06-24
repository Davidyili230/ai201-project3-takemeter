#!/usr/bin/env python3
"""
Collects real r/nba posts using Reddit's official OAuth API (no IP blocks).

Setup (one time):
  1. Go to https://www.reddit.com/prefs/apps
  2. Click "create another app" → type: script
  3. Paste your client_id and client_secret below (or set as env vars)

Usage:
    pip install requests
    python3 collect_reddit.py

Output: nba_dataset_unlabeled.csv  (open in Excel/Sheets, fill in 'label' column)
"""

import os, csv, time, requests
from base64 import b64encode

# ── Fill these in (or set as env vars REDDIT_CLIENT_ID / REDDIT_CLIENT_SECRET) ──
CLIENT_ID     = os.getenv("REDDIT_CLIENT_ID",     "YOUR_CLIENT_ID_HERE")
CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET", "YOUR_CLIENT_SECRET_HERE")
USERNAME      = os.getenv("REDDIT_USERNAME",       "YOUR_REDDIT_USERNAME")
PASSWORD      = os.getenv("REDDIT_PASSWORD",       "YOUR_REDDIT_PASSWORD")
# ─────────────────────────────────────────────────────────────────────────────────

SUBREDDIT = "nba"
OUTPUT    = "nba_dataset_unlabeled.csv"
USER_AGENT = f"python:nba-classifier:v1.0 (by /u/{USERNAME})"

FEEDS = [
    ("hot",           f"subreddits/mine/hot",                   {}),
    ("top_month",     f"r/{SUBREDDIT}/top",                     {"t": "month"}),
    ("top_week",      f"r/{SUBREDDIT}/top",                     {"t": "week"}),
    ("controversial", f"r/{SUBREDDIT}/controversial",           {"t": "month"}),
    ("new",           f"r/{SUBREDDIT}/new",                     {}),
]
# Overwrite with direct subreddit paths
FEEDS = [
    ("hot",           f"r/{SUBREDDIT}/hot",           {}),
    ("top_month",     f"r/{SUBREDDIT}/top",           {"t": "month"}),
    ("top_week",      f"r/{SUBREDDIT}/top",           {"t": "week"}),
    ("controversial", f"r/{SUBREDDIT}/controversial", {"t": "month"}),
    ("new",           f"r/{SUBREDDIT}/new",           {}),
]


def get_token():
    creds = b64encode(f"{CLIENT_ID}:{CLIENT_SECRET}".encode()).decode()
    r = requests.post(
        "https://www.reddit.com/api/v1/access_token",
        headers={
            "Authorization": f"Basic {creds}",
            "User-Agent": USER_AGENT,
        },
        data={"grant_type": "password", "username": USERNAME, "password": PASSWORD},
        timeout=15,
    )
    r.raise_for_status()
    token = r.json().get("access_token")
    if not token:
        raise RuntimeError(f"Token error: {r.json()}")
    return token


def fetch_feed(token, endpoint, params, limit=100):
    headers = {"Authorization": f"bearer {token}", "User-Agent": USER_AGENT}
    params  = {**params, "limit": limit, "raw_json": 1}
    r = requests.get(
        f"https://oauth.reddit.com/{endpoint}",
        headers=headers, params=params, timeout=15,
    )
    r.raise_for_status()
    return r.json()["data"]["children"]


def make_text(title, selftext):
    title    = (title or "").strip()
    selftext = (selftext or "").strip()
    if selftext and selftext not in ("[removed]", "[deleted]"):
        combined = f"{title}. {selftext}"
    else:
        combined = title
    return combined[:600]


def main():
    if "YOUR_CLIENT_ID" in CLIENT_ID:
        print("ERROR: Set CLIENT_ID, CLIENT_SECRET, USERNAME, PASSWORD at the top of this script.")
        return

    print("Authenticating with Reddit OAuth...")
    token = get_token()
    print("Token OK.\n")

    all_posts, seen_ids = [], set()

    for feed_name, endpoint, params in FEEDS:
        print(f"Fetching {feed_name}...")
        try:
            children = fetch_feed(token, endpoint, params)
            new = 0
            for child in children:
                d = child["data"]
                pid = d.get("id", "")
                if pid in seen_ids:
                    continue
                text = make_text(d.get("title"), d.get("selftext"))
                if len(text) < 50:
                    continue
                seen_ids.add(pid)
                all_posts.append({
                    "text":            text,
                    "label":           "",
                    "source":          feed_name,
                    "annotator_notes": "",
                    "reddit_id":       pid,
                    "permalink":       f"https://reddit.com{d.get('permalink', '')}",
                })
                new += 1
            print(f"  {new} new posts")
        except Exception as e:
            print(f"  Error: {e}")
        time.sleep(1)

    fieldnames = ["text", "label", "source", "annotator_notes", "reddit_id", "permalink"]
    with open(OUTPUT, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
        writer.writeheader()
        writer.writerows(all_posts)

    print(f"\nWrote {len(all_posts)} posts to {OUTPUT}")
    print("Open the CSV, read each post, fill in 'label': hot_take | analysis | reaction")
    print("Skip off-topic posts (game recaps, trade news, injury reports that are pure news).")


if __name__ == "__main__":
    main()
