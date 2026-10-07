#!/usr/bin/env python3
"""Fetch Last.fm top tags per artist -> ~/.cache/spotify-tags.json"""
import json, os, time, urllib.parse, urllib.request
C = os.path.expanduser("~/.cache")
key = next(l.split("=", 1)[1].strip() for l in open(os.path.expanduser("~/.config/last.fm/client.env")) if l.startswith("LASTFM_API_KEY="))
d = json.load(open(f"{C}/spotify-library.json"))
names = sorted({a for p in d["playlists"] for t in p["tracks"] for a in t["artists"]})
out = json.load(open(f"{C}/spotify-tags.json")) if os.path.exists(f"{C}/spotify-tags.json") else {}
for n in names:
    if n in out: continue
    u = "https://ws.audioscrobbler.com/2.0/?" + urllib.parse.urlencode({"method": "artist.gettoptags", "artist": n, "api_key": key, "format": "json", "autocorrect": 1})
    try:
        r = json.load(urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "spotify-playlist-sorter/0.1"}), timeout=20))
        out[n] = [(t["name"].lower(), t["count"]) for t in r.get("toptags", {}).get("tag", [])[:8]]
    except Exception as e:
        print("!", n, e); out[n] = None
    time.sleep(0.25)
json.dump(out, open(f"{C}/spotify-tags.json", "w"))
print(f"tags for {sum(1 for v in out.values() if v)}/{len(names)} artists")
