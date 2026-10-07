#!/usr/bin/env python3
"""Draft genre/tempo/mood buckets from the cached library. Writes ~/.cache/spotify-draft.json and draft-playlists.md"""
import json, os, collections as C
c = os.path.expanduser("~/.cache/")
d = json.load(open(c+"spotify-library.json")); tg = json.load(open(c+"spotify-tags.json")); ft = json.load(open(c+"spotify-features.json"))
fp = {t["id"] for t in json.load(open(c+"frequent-play.json"))}
tracks = {}
for p in d["playlists"]:
    for t in p["tracks"]:
        tracks.setdefault(t["id"], t)
def tags(t):
    w = C.Counter()
    for i, a in enumerate(t["artists"][:2]):
        for n, cnt in (tg.get(a) or [])[:6]: w[n] += cnt / (1 + i)
    return w
HARD = {"aggrotech", "dark electro", "industrial", "hard ebm", "electro-industrial", "industrial metal", "harsh ebm", "darkelectro", "terror ebm"}
DARK = {"darkwave", "gothic rock", "goth", "post-punk", "gothic", "cold wave", "dark wave", "deathrock"}
SYNTH = {"synthpop", "new wave", "80s", "electropop", "synth-pop", "synth pop", "italo disco"}
FUT = {"futurepop", "ebm", "electronic", "electro", "electro-industrial"}
def bucket(t):
    w = tags(t); f = ft.get(t["id"]) or {}
    tempo, en, val = f.get("tempo"), f.get("energy"), f.get("valence")
    s = lambda S: sum(v for k, v in w.items() if k in S)
    if not w: return "Unsorted (no tags)"
    if en is not None and en < 0.5: return "Slow & Soft"
    top = max(("hard", s(HARD)), ("dark", s(DARK)), ("synth", s(SYNTH)), ("fut", s(FUT)), key=lambda x: x[1])
    if top[1] == 0: return "Outside the Scene" if (en is None or en < 0.7) else "Unsorted (no tags)"
    k = top[0]
    if k == "hard": return "Hard Edge (Aggrotech / Industrial)"
    if k == "dark": return "Darkwave & Goth"
    if k == "synth": return "Synthpop & New Wave" if (val is None or val >= 0.4) else "Melancholy Synth"
    if tempo and tempo < 118 or (val is not None and val < 0.3 and (tempo or 0) < 130): return "Melancholy Synth"
    return "Futurepop & EBM: Dancefloor (130+ BPM)" if tempo and tempo >= 130 else "Futurepop & EBM: Mid-tempo"
out = C.defaultdict(list)
for t in tracks.values():
    f = ft.get(t["id"]) or {}
    out[bucket(t)].append({**{k: t[k] for k in ("id", "uri", "name")}, "artist": t["artists"][0], "tempo": f.get("tempo"), "energy": f.get("energy"), "valence": f.get("valence"), "freq": t["id"] in fp})
json.dump(out, open(c+"spotify-draft.json", "w"))
md = ["# Draft playlists (proposal, nothing created in Spotify)\n"]
for b, ts in sorted(out.items(), key=lambda x: -len(x[1])):
    tp = [t["tempo"] for t in ts if t["tempo"]]
    md.append(f"## {b} ({len(ts)} tracks" + (f", median {round(sorted(tp)[len(tp)//2])} BPM" if tp else "") + ")")
    md += [f"- {t['artist']} - {t['name']}" + (f" [{round(t['tempo'])}]" if t["tempo"] else "") for t in sorted(ts, key=lambda t: (t["tempo"] or 0))]
    md.append("")
open("draft-playlists.md", "w").write("\n".join(md))
for b, ts in sorted(out.items(), key=lambda x: -len(x[1])):
    print(len(ts), b, "|", ", ".join(C.Counter(t["artist"] for t in ts).most_common(4)[i][0] for i in range(min(4, len(set(t["artist"] for t in ts))))))
