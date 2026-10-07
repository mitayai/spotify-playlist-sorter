#!/usr/bin/env python3
"""Create the approved draft buckets as PRIVATE playlists. Idempotent via ~/.cache/spotify-created.json"""
import json, os, urllib.error, urllib.request, spotify as s
c = os.path.expanduser("~/.cache/")
draft = json.load(open(c+"spotify-draft.json"))
done = json.load(open(c+"spotify-created.json")) if os.path.exists(c+"spotify-created.json") else {}
def call(method, path, body):
    req = urllib.request.Request(s.API + path, json.dumps(body).encode(), {"Authorization": "Bearer " + s.token(), "Content-Type": "application/json"}, method=method)
    return json.load(urllib.request.urlopen(req))
for name, ts in draft.items():
    if name.startswith("Unsorted") or name in done: continue
    try: pl = call("POST", "/me/playlists", {"name": name, "public": False, "description": "Sorted by genre, tempo and mood (Claude draft)"})
    except urllib.error.HTTPError as e: print("create failed", name, e.code, e.read()[:200]); break
    uris = [t["uri"] for t in sorted(ts, key=lambda t: (t["tempo"] or 0))]
    for i in range(0, len(uris), 100):
        try: call("POST", f"/playlists/{pl['id']}/items", {"uris": uris[i:i+100]})
        except urllib.error.HTTPError as e: print("add failed", name, e.code, e.read()[:200]); break
    done[name] = pl["id"]; json.dump(done, open(c+"spotify-created.json", "w"))
    print(f"created {name}: {len(uris)} tracks, public={pl.get('public')}")
