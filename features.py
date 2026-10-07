#!/usr/bin/env python3
"""Fetch tempo/energy/etc. from ReccoBeats for every track in the dump -> ~/.cache/spotify-features.json"""
import json, os, re, time, urllib.request
C = os.path.expanduser("~/.cache")
d = json.load(open(f"{C}/spotify-library.json"))
ids = sorted({t["id"] for p in d["playlists"] for t in p["tracks"]})
out = {}
for i in range(0, len(ids), 40):
    u = "https://api.reccobeats.com/v1/audio-features?ids=" + ",".join(ids[i:i+40])
    r = json.load(urllib.request.urlopen(urllib.request.Request(u, headers={"Accept": "application/json", "User-Agent": "spotify-playlist-sorter/0.1"}), timeout=30))
    for f in r["content"]:
        m = re.search(r"/track/(\w+)", f.get("href", ""))
        if m: out[m.group(1)] = {k: f.get(k) for k in ("tempo", "energy", "danceability", "valence", "acousticness", "instrumentalness", "loudness", "mode", "key")}
    time.sleep(0.5)
json.dump(out, open(f"{C}/spotify-features.json", "w"))
print(f"features for {len(out)}/{len(ids)} tracks")
