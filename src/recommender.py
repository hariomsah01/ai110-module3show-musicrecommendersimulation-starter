import csv
from typing import List, Dict, Tuple
from dataclasses import dataclass, asdict

# --- Algorithm Recipe weights (see README "How The System Works") ---
GENRE_WEIGHT = 2.0
MOOD_WEIGHT = 1.0
ENERGY_WEIGHT = 1.0
ACOUSTIC_WEIGHT = 0.5

# Columns in songs.csv that must become numbers so we can do math on them.
NUMERIC_FIELDS = ("energy", "tempo_bpm", "valence", "danceability", "acousticness")


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


@dataclass
class UserProfile:
    """Represents a user's taste preferences."""
    favorite_genre: str
    favorite_mood: str
    target_energy: float
    likes_acoustic: bool


class Recommender:
    """OOP wrapper that scores and ranks Song objects for a UserProfile."""

    def __init__(self, songs: List[Song]):
        self.songs = songs

    def _prefs_from_user(self, user: UserProfile) -> Dict:
        """Map a UserProfile onto the dict keys score_song() expects."""
        return {
            "genre": user.favorite_genre,
            "mood": user.favorite_mood,
            "energy": user.target_energy,
            "likes_acoustic": user.likes_acoustic,
        }

    def recommend(self, user: UserProfile, k: int = 5) -> List[Song]:
        """Return the top-k Song objects ranked by score, highest first."""
        prefs = self._prefs_from_user(user)
        scored = [(song, score_song(prefs, asdict(song))[0]) for song in self.songs]
        scored.sort(key=lambda pair: pair[1], reverse=True)
        return [song for song, _ in scored[:k]]

    def explain_recommendation(self, user: UserProfile, song: Song) -> str:
        """Return a human-readable explanation of why a song was recommended."""
        score, reasons = score_song(self._prefs_from_user(user), asdict(song))
        if not reasons:
            return f"{song.title} scored {score:.2f} with no strong feature matches."
        return f"{song.title} (score {score:.2f}): " + "; ".join(reasons)


def load_songs(csv_path: str) -> List[Dict]:
    """Load songs.csv into a list of dicts, converting numeric columns to numbers."""
    songs: List[Dict] = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            row["id"] = int(row["id"])
            for field in NUMERIC_FIELDS:
                if row.get(field) not in (None, ""):
                    row[field] = float(row[field])
            songs.append(row)
    return songs


def score_song(user_prefs: Dict, song: Dict) -> Tuple[float, List[str]]:
    """Score one song against the user's preferences, returning (score, reasons)."""
    score = 0.0
    reasons: List[str] = []

    # Genre match — the strongest single signal of taste.
    if user_prefs.get("genre") and user_prefs["genre"] == song.get("genre"):
        score += GENRE_WEIGHT
        reasons.append(f"genre match: {song['genre']} (+{GENRE_WEIGHT})")

    # Mood match — a meaningful but secondary signal.
    if user_prefs.get("mood") and user_prefs["mood"] == song.get("mood"):
        score += MOOD_WEIGHT
        reasons.append(f"mood match: {song['mood']} (+{MOOD_WEIGHT})")

    # Energy closeness — rewards songs whose energy is NEAR the target,
    # not just songs with high energy.
    if "energy" in user_prefs and song.get("energy") is not None:
        closeness = 1 - abs(float(song["energy"]) - float(user_prefs["energy"]))
        points = ENERGY_WEIGHT * closeness
        score += points
        reasons.append(
            f"energy {song['energy']} close to target {user_prefs['energy']} (+{points:.2f})"
        )

    # Acoustic preference — treat acousticness >= 0.5 as an "acoustic" track.
    if user_prefs.get("likes_acoustic") is not None and "acousticness" in song:
        song_is_acoustic = float(song["acousticness"]) >= 0.5
        if bool(user_prefs["likes_acoustic"]) == song_is_acoustic:
            score += ACOUSTIC_WEIGHT
            reasons.append(f"acoustic preference match (+{ACOUSTIC_WEIGHT})")

    return score, reasons


def recommend_songs(
    user_prefs: Dict, songs: List[Dict], k: int = 5
) -> List[Tuple[Dict, float, str]]:
    """Score every song, then return the top-k as (song, score, explanation) sorted high→low."""
    scored: List[Tuple[Dict, float, str]] = []
    for song in songs:
        score, reasons = score_song(user_prefs, song)
        explanation = "; ".join(reasons) if reasons else "no strong matches"
        scored.append((song, score, explanation))

    # sorted() returns a new list and leaves `songs` untouched (see README notes).
    ranked = sorted(scored, key=lambda item: item[1], reverse=True)
    return ranked[:k]
