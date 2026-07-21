"""
Command line runner for the Music Recommender Simulation.

Demonstrates all four optional extensions:
  1. Advanced song features (popularity, decade, mood tags, language)
  2. Switchable scoring modes (balanced / genre-first / mood-first / energy-focused)
  3. A diversity penalty so one artist/genre can't dominate the list
  4. A formatted results table (tabulate, with an ASCII fallback)

Run it from the project root with:  python -m src.main
"""

import textwrap

from src.recommender import load_songs, recommend_songs, STRATEGIES

try:
    from tabulate import tabulate
    HAVE_TABULATE = True
except ImportError:  # graceful fallback if tabulate isn't installed
    HAVE_TABULATE = False


# Some profiles exercise the new advanced features (target_decade, desired_tags,
# prefers_popular). The last two are adversarial / conflicting on purpose.
PROFILES = [
    ("High-Energy Pop", {"genre": "pop", "mood": "happy", "energy": 0.9, "prefers_popular": True}),
    ("Chill Lofi", {"genre": "lofi", "mood": "chill", "energy": 0.3, "likes_acoustic": True,
                    "desired_tags": ["calm", "study"]}),
    ("2000s Nostalgia", {"genre": "country", "mood": "nostalgic", "energy": 0.5,
                          "target_decade": 2000, "desired_tags": ["warm", "wistful"]}),
    ("Deep Intense Rock", {"genre": "rock", "mood": "intense", "energy": 0.95}),
    ("Conflicted (loud + sad)", {"genre": "folk", "mood": "sad", "energy": 0.95}),
]


def render_table(recs) -> str:
    """Format (song, score, reasons) rows as a table, including the reasons column."""
    headers = ["#", "Title", "Artist", "Score", "Reasons"]
    rows = [
        [i, song["title"], song["artist"], f"{score:.2f}", reasons]
        for i, (song, score, reasons) in enumerate(recs, 1)
    ]

    if HAVE_TABULATE:
        return tabulate(rows, headers=headers, tablefmt="grid",
                        maxcolwidths=[3, 20, 16, 6, 46])
    return _ascii_table(headers, rows)


def _ascii_table(headers, rows) -> str:
    """Minimal dependency-free table with word-wrapped cells."""
    widths = [3, 20, 16, 6, 46]

    def fmt(cells):
        wrapped = [textwrap.wrap(str(c), w) or [""] for c, w in zip(cells, widths)]
        height = max(len(col) for col in wrapped)
        lines = []
        for i in range(height):
            cols = [(wrapped[j][i] if i < len(wrapped[j]) else "").ljust(widths[j])
                    for j in range(len(cells))]
            lines.append("| " + " | ".join(cols) + " |")
        return "\n".join(lines)

    sep = "+" + "+".join("-" * (w + 2) for w in widths) + "+"
    out = [sep, fmt(headers), sep]
    for r in rows:
        out.append(fmt(r))
        out.append(sep)
    return "\n".join(out)


def main() -> None:
    songs = load_songs("data/songs.csv")
    print(f"Loaded songs: {len(songs)}")

    # --- Main run: balanced mode + diversity penalty on every profile ---
    for label, prefs in PROFILES:
        prefs_str = ", ".join(f"{k}={v}" for k, v in prefs.items())
        recs = recommend_songs(prefs, songs, k=5, diversity_penalty=0.75)
        print(f"\n===== {label} (mode: balanced, diversity on) =====")
        print(f"Profile: {prefs_str}")
        print(render_table(recs))

    # --- Challenge 2 demo: same profile, different scoring modes ---
    demo_prefs = {"genre": "pop", "mood": "chill", "energy": 0.5}
    print("\n\n########## Scoring-mode comparison ##########")
    print(f"Profile: {demo_prefs}")
    for mode in ("genre-first", "mood-first", "energy-focused"):
        recs = recommend_songs(demo_prefs, songs, k=3, strategy=STRATEGIES[mode])
        print(f"\n----- mode: {mode} -----")
        print(render_table(recs))


if __name__ == "__main__":
    main()
