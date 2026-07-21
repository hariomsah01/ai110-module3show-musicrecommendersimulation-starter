import csv
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, asdict

# --- Base Algorithm Recipe weights (see README "How The System Works") ---
GENRE_WEIGHT = 2.0
MOOD_WEIGHT = 1.0
ENERGY_WEIGHT = 1.0
ACOUSTIC_WEIGHT = 0.5
# Weights for the advanced (Challenge 1) features:
DECADE_WEIGHT = 1.0       # exact release-decade match
TAG_WEIGHT = 0.5          # per overlapping detailed mood tag
POPULARITY_WEIGHT = 1.0   # scaled by popularity/100 when the user prefers popular
LANGUAGE_WEIGHT = 0.5     # language match

# Columns in songs.csv and how to convert them.
INT_FIELDS = ("id", "popularity", "release_decade")
FLOAT_FIELDS = (
    "energy", "tempo_bpm", "valence", "danceability", "acousticness", "instrumentalness",
)


@dataclass
class Song:
    """Represents a song and its attributes."""
    id: int
    title: str
    artist: str
    genre: str
    mood: str
    energy: float
    tempo_bpm: float
    valence: float
    danceability: float
    acousticness: float
    # Advanced (Challenge 1) attributes — defaulted so existing tests still construct Song.
    popularity: int = 0
    release_decade: int = 0
    mood_tags: str = ""
    instrumentalness: float = 0.0
    language: str = ""


@dataclass
class UserProfile:
    """Represents a user's taste preferences."""
    favorite_genre: str
    favorite_mood: str
    target_energy: float
    likes_acoustic: bool


# ---------------------------------------------------------------------------
# Challenge 2: Strategy pattern for interchangeable scoring modes.
# Each strategy is the SAME algorithm with a different weight table, so a user
# can switch "what matters most" without touching the scoring code.
# ---------------------------------------------------------------------------
class ScoringStrategy:
    """Base scoring mode; subclasses just override `name` and `weights`."""

    name = "balanced"
    weights = {
        "genre": GENRE_WEIGHT,
        "mood": MOOD_WEIGHT,
        "energy": ENERGY_WEIGHT,
        "acoustic": ACOUSTIC_WEIGHT,
        "decade": DECADE_WEIGHT,
        "tags": TAG_WEIGHT,
        "popularity": POPULARITY_WEIGHT,
        "language": LANGUAGE_WEIGHT,
    }

    def score(self, user_prefs: Dict, song: Dict) -> Tuple[float, List[str]]:
        """Score one song against the user's prefs, returning (score, reasons)."""
        w = self.weights
        score = 0.0
        reasons: List[str] = []

        # --- Core features ---
        if user_prefs.get("genre") and user_prefs["genre"] == song.get("genre"):
            score += w["genre"]
            reasons.append(f"genre match: {song['genre']} (+{w['genre']})")

        if user_prefs.get("mood") and user_prefs["mood"] == song.get("mood"):
            score += w["mood"]
            reasons.append(f"mood match: {song['mood']} (+{w['mood']})")

        # Energy closeness: reward songs NEAR the target, not just loud ones.
        if "energy" in user_prefs and song.get("energy") is not None:
            closeness = 1 - abs(float(song["energy"]) - float(user_prefs["energy"]))
            points = w["energy"] * closeness
            score += points
            reasons.append(
                f"energy {song['energy']} close to target {user_prefs['energy']} (+{points:.2f})"
            )

        if user_prefs.get("likes_acoustic") is not None and "acousticness" in song:
            song_is_acoustic = float(song["acousticness"]) >= 0.5
            if bool(user_prefs["likes_acoustic"]) == song_is_acoustic:
                score += w["acoustic"]
                reasons.append(f"acoustic preference match (+{w['acoustic']})")

        # --- Advanced (Challenge 1) features, only scored if the user asks ---
        if user_prefs.get("target_decade") and song.get("release_decade"):
            if int(user_prefs["target_decade"]) == int(song["release_decade"]):
                score += w["decade"]
                reasons.append(f"from the {song['release_decade']}s (+{w['decade']})")

        if user_prefs.get("desired_tags") and song.get("mood_tags"):
            song_tags = set(str(song["mood_tags"]).split("|"))
            overlap = song_tags.intersection(user_prefs["desired_tags"])
            if overlap:
                points = w["tags"] * len(overlap)
                score += points
                reasons.append(f"mood tags {sorted(overlap)} (+{points:.2f})")

        if user_prefs.get("prefers_popular") and song.get("popularity") is not None:
            points = w["popularity"] * (float(song["popularity"]) / 100.0)
            score += points
            reasons.append(f"popularity {song['popularity']} (+{points:.2f})")

        if user_prefs.get("language") and song.get("language"):
            if user_prefs["language"] == song["language"]:
                score += w["language"]
                reasons.append(f"language match: {song['language']} (+{w['language']})")

        return score, reasons


class GenreFirst(ScoringStrategy):
    """Genre matters most; mood and energy are tie-breakers."""
    name = "genre-first"
    weights = {**ScoringStrategy.weights, "genre": 3.0, "mood": 0.5, "energy": 0.5}


class MoodFirst(ScoringStrategy):
    """Mood/feeling matters most, regardless of genre."""
    name = "mood-first"
    weights = {**ScoringStrategy.weights, "genre": 0.5, "mood": 3.0, "energy": 0.5}


class EnergyFocused(ScoringStrategy):
    """Getting the energy level right matters most (great for workouts/focus)."""
    name = "energy-focused"
    weights = {**ScoringStrategy.weights, "genre": 0.5, "mood": 0.5, "energy": 3.0}


DEFAULT_STRATEGY = ScoringStrategy()
STRATEGIES: Dict[str, ScoringStrategy] = {
    s.name: s for s in [DEFAULT_STRATEGY, GenreFirst(), MoodFirst(), EnergyFocused()]
}


class Recommender:
    """OOP wrapper that scores and ranks Song objects for a UserProfile."""

    def __init__(self, songs: List[Song], strategy: Optional[ScoringStrategy] = None):
        self.songs = songs
        self.strategy = strategy or DEFAULT_STRATEGY

    def _prefs_from_user(self, user: UserProfile) -> Dict:
        """Map a UserProfile onto the dict keys the scorer expects."""
        return {
            "genre": user.favorite_genre,
            "mood": user.favorite_mood,
            "energy": user.target_energy,
            "likes_acoustic": user.likes_acoustic,
        }

    def recommend(self, user: UserProfile, k: int = 5) -> List[Song]:
        """Return the top-k Song objects ranked by score, highest first."""
        prefs = self._prefs_from_user(user)
        scored = [(song, self.strategy.score(prefs, asdict(song))[0]) for song in self.songs]
        scored.sort(key=lambda pair: pair[1], reverse=True)
        return [song for song, _ in scored[:k]]

    def explain_recommendation(self, user: UserProfile, song: Song) -> str:
        """Return a human-readable explanation of why a song was recommended."""
        score, reasons = self.strategy.score(self._prefs_from_user(user), asdict(song))
        if not reasons:
            return f"{song.title} scored {score:.2f} with no strong feature matches."
        return f"{song.title} (score {score:.2f}): " + "; ".join(reasons)


def load_songs(csv_path: str) -> List[Dict]:
    """Load songs.csv into a list of dicts, converting numeric columns to numbers."""
    songs: List[Dict] = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            for field_name in INT_FIELDS:
                if row.get(field_name) not in (None, ""):
                    row[field_name] = int(row[field_name])
            for field_name in FLOAT_FIELDS:
                if row.get(field_name) not in (None, ""):
                    row[field_name] = float(row[field_name])
            songs.append(row)
    return songs


def score_song(
    user_prefs: Dict, song: Dict, strategy: Optional[ScoringStrategy] = None
) -> Tuple[float, List[str]]:
    """Score one song against the user's preferences using the given strategy."""
    return (strategy or DEFAULT_STRATEGY).score(user_prefs, song)


def recommend_songs(
    user_prefs: Dict,
    songs: List[Dict],
    k: int = 5,
    strategy: Optional[ScoringStrategy] = None,
    diversity_penalty: float = 0.0,
) -> List[Tuple[Dict, float, str]]:
    """Score every song and return the top-k as (song, score, explanation), high→low.

    If diversity_penalty > 0, greedily penalizes songs whose artist or genre is
    already represented in the picks so far, spreading the list out (Challenge 3).
    """
    strategy = strategy or DEFAULT_STRATEGY
    scored = []
    for song in songs:
        s, reasons = strategy.score(user_prefs, song)
        scored.append({"song": song, "base": s, "reasons": list(reasons)})

    # sorted() returns a new list and leaves `songs` untouched (see README notes).
    ranked = sorted(scored, key=lambda d: d["base"], reverse=True)

    if diversity_penalty <= 0:
        top = ranked[:k]
        return [
            (d["song"], d["base"], "; ".join(d["reasons"]) or "no strong matches")
            for d in top
        ]

    # --- Challenge 3: greedy diversity-aware selection ---
    selected: List[Tuple[Dict, float, str]] = []
    seen_artists: Dict[str, int] = {}
    seen_genres: Dict[str, int] = {}
    remaining = list(ranked)

    while remaining and len(selected) < k:
        best, best_adj, best_pen = None, None, 0.0
        for d in remaining:
            artist = d["song"].get("artist")
            genre = d["song"].get("genre")
            penalty = diversity_penalty * (seen_artists.get(artist, 0) + seen_genres.get(genre, 0))
            adjusted = d["base"] - penalty
            if best is None or adjusted > best_adj:
                best, best_adj, best_pen = d, adjusted, penalty

        remaining.remove(best)
        reasons = list(best["reasons"])
        if best_pen > 0:
            reasons.append(f"diversity penalty (-{best_pen:.2f})")
        selected.append((best["song"], best_adj, "; ".join(reasons) or "no strong matches"))

        artist = best["song"].get("artist")
        genre = best["song"].get("genre")
        seen_artists[artist] = seen_artists.get(artist, 0) + 1
        seen_genres[genre] = seen_genres.get(genre, 0) + 1

    return selected
