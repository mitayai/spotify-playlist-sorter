# Spotify playlist sorter

Small, dependency-free Python scripts that read your own Spotify playlists and sort the tracks into new, private playlists by genre, tempo and mood. They were written with Claude Code to reorganise a personal library of futurepop, EBM, synthpop and darkwave into playlists that are actually usable for a mood or a BPM range.

## What it does

1. `spotify.py login` – one-time browser approval (OAuth Authorization Code with PKCE, so no client secret is needed). Token is stored in `~/.config/spotify/token.json` (mode 0600).
2. `spotify.py dump` – downloads every playlist you own with its tracks to `~/.cache/spotify-library.json`.
3. `features.py` – fetches tempo, energy, valence, danceability, etc. for each track from [ReccoBeats](https://reccobeats.com).
4. `tags.py` – fetches genre tags per artist from [Last.fm](https://www.last.fm/api).
5. `classify.py` – groups tracks into buckets using the tags plus tempo/energy/valence rules (edit the sets and thresholds to taste) and writes a draft to review.
6. `create.py` – creates the approved buckets as **private** playlists (idempotent, so a re-run does not duplicate).

## Setup

- Create a Spotify app at <https://developer.spotify.com/dashboard> with redirect URI `http://127.0.0.1:8888/callback` and the Web API enabled.
- Create a Last.fm API key at <https://www.last.fm/api/account/create>.
- Put the keys outside the repo:

```
~/.config/spotify/client.env   SPOTIFY_CLIENT_ID=...
~/.config/last.fm/client.env   LASTFM_API_KEY=...
```

Then run the scripts in the order above. Review the draft from `classify.py` before running `create.py`.

## Why the extra services

Spotify has restricted its API for new apps, so some data has to come from elsewhere:

- Genres are no longer returned on artist objects, so Last.fm tags are used.
- The audio-features endpoint (tempo, energy) is unavailable, so ReccoBeats is used. It does not cover every track (about 70% in testing); tracks without it are sorted by genre only.
- Algorithmic playlists (On Repeat, Discover Weekly) and other people's playlists cannot be read. To analyse one, copy it into a playlist of your own first.

## Notes

- Nothing is written to Spotify except the playlists you approve in `create.py`.
- Requires Python 3.9+; standard library only.
- Unofficial and unaffiliated with Spotify, Last.fm or ReccoBeats. Respect each service's terms.
