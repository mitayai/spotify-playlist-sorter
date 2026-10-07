#!/usr/bin/env python3
"""Spotify Web API helper (PKCE, stdlib only).

  spotify.py login            one-time browser approval
  spotify.py dump [OUT.json]  fetch own playlists + tracks + artist genres
Token lives in ~/.config/spotify/token.json (0600), never in the repo.
"""
import base64, hashlib, http.server, json, os, secrets, sys, time, urllib.parse, urllib.request, urllib.error, webbrowser

CFG = os.path.expanduser("~/.config/spotify")
TOKEN = f"{CFG}/token.json"
REDIRECT = "http://127.0.0.1:8888/callback"
SCOPES = "playlist-read-private playlist-read-collaborative playlist-modify-private playlist-modify-public user-library-read"
API = "https://api.spotify.com/v1"

def client_id():
    for line in open(f"{CFG}/client.env"):
        if line.startswith("SPOTIFY_CLIENT_ID="):
            return line.split("=", 1)[1].strip()
    sys.exit("no client id")

def post(data):
    req = urllib.request.Request("https://accounts.spotify.com/api/token", urllib.parse.urlencode(data).encode())
    return json.load(urllib.request.urlopen(req))

def save(tok, old=None):
    tok["expires_at"] = time.time() + tok["expires_in"] - 60
    tok.setdefault("refresh_token", (old or {}).get("refresh_token"))
    fd = os.open(TOKEN, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as f:
        json.dump(tok, f)
    return tok

def login():
    verifier = secrets.token_urlsafe(64)
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b"=").decode()
    state = secrets.token_urlsafe(16)
    url = "https://accounts.spotify.com/authorize?" + urllib.parse.urlencode({
        "client_id": client_id(), "response_type": "code", "redirect_uri": REDIRECT,
        "scope": SCOPES, "state": state, "code_challenge_method": "S256", "code_challenge": challenge})
    got = {}
    class H(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            got.update(urllib.parse.parse_qsl(urllib.parse.urlparse(self.path).query))
            self.send_response(200); self.end_headers()
            self.wfile.write(b"Done. You can close this tab.")
        def log_message(self, *a): pass
    srv = http.server.HTTPServer(("127.0.0.1", 8888), H)
    print("Open this URL if a browser doesn't appear:\n" + url, flush=True)
    webbrowser.open(url)
    srv.handle_request()
    if got.get("state") != state or "code" not in got:
        sys.exit(f"auth failed: {got}")
    save(post({"grant_type": "authorization_code", "code": got["code"], "redirect_uri": REDIRECT,
               "client_id": client_id(), "code_verifier": verifier}))
    print("Logged in; token saved.")

def token():
    tok = json.load(open(TOKEN))
    if time.time() > tok["expires_at"]:
        tok = save(post({"grant_type": "refresh_token", "refresh_token": tok["refresh_token"],
                         "client_id": client_id()}), tok)
    return tok["access_token"]

def get(path, **params):
    url = path if path.startswith("http") else API + path
    if params:
        url += "?" + urllib.parse.urlencode(params)
    for attempt in range(6):
        req = urllib.request.Request(url, headers={"Authorization": "Bearer " + token()})
        try:
            return json.load(urllib.request.urlopen(req))
        except urllib.error.HTTPError as e:
            if e.code == 429:
                time.sleep(int(e.headers.get("Retry-After", 2)) + 1); continue
            raise

def pages(path, **params):
    page = get(path, limit=50, **params)
    while page:
        yield from page["items"]
        page = get(page["next"]) if page.get("next") else None

def dump(out):
    me = get("/me")
    print("user:", me["id"], me.get("product"), flush=True)
    result, artists = [], {}
    for pl in pages("/me/playlists"):
        if not pl: continue
        owned = pl["owner"]["id"] == me["id"]
        tracks = []
        if owned or pl.get("collaborative"):
            try:
                for it in pages(f"/playlists/{pl['id']}/items"):
                    t = (it or {}).get("track") or (it or {}).get("item")
                    if t and t.get("id"):
                        tracks.append({"id": t["id"], "name": t["name"], "uri": t["uri"],
                                       "album": t["album"]["name"], "artist_ids": [a["id"] for a in t["artists"] if a.get("id")],
                                       "artists": [a["name"] for a in t["artists"]]})
            except urllib.error.HTTPError as e:
                print(f"  ! {pl['name']}: HTTP {e.code}", file=sys.stderr)
        result.append({"id": pl["id"], "name": pl["name"], "owned": owned, "public": pl.get("public"),
                       "total": (pl.get("items") or pl.get("tracks") or {}).get("total"), "tracks": tracks})
        print(f"{'*' if owned else ' '} {pl['name']}: {len(tracks)} tracks", flush=True)
    ids = sorted({a for p in result for t in p["tracks"] for a in t["artist_ids"]})
    for i in range(0, len(ids), 50):
        try:
            for a in get("/artists", ids=",".join(ids[i:i+50]))["artists"]:
                if a: artists[a["id"]] = {"name": a["name"], "genres": a.get("genres", []), "popularity": a.get("popularity")}
        except urllib.error.HTTPError as e:
            print(f"  ! artists batch: HTTP {e.code}", file=sys.stderr); break
    json.dump({"user": me["id"], "playlists": result, "artists": artists}, open(out, "w"), indent=1)
    print(f"wrote {out}: {len(result)} playlists, {len(artists)} artists")

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "login": login()
    elif cmd == "dump": dump(sys.argv[2] if len(sys.argv) > 2 else os.path.expanduser("~/.cache/spotify-library.json"))
    else: print(__doc__)
