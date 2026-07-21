# 🎵 Music Recommender Simulation

## Project Summary

In this project you will build and explain a small music recommender system.

Your goal is to:

- Represent songs and a user "taste profile" as data
- Design a scoring rule that turns that data into recommendations
- Evaluate what your system gets right and wrong
- Reflect on how this mirrors real world AI recommenders

Replace this paragraph with your own summary of what your version does.

---

## How The System Works

Real streaming platforms like Spotify and YouTube mix two ideas.
**Collaborative filtering** guesses what you'll like from the behavior of
*other* listeners with similar taste ("people who liked this also liked
that"), while **content-based filtering** looks at the *attributes of the
songs themselves* and matches them to what you've liked before. Big platforms
blend both, but they lean on collaborative filtering to surprise you and
content-based filtering to explain and cold-start new tracks.

My version is **purely content-based**. It does not know anything about other
users — it only compares song attributes against a single user's stated taste.
This keeps it simple and, importantly, **explainable**: every recommendation
can come with a plain reason like "chill lofi with energy close to yours."
My system prioritizes matching **genre and mood** first, then getting the
**energy level** close to what the user wants.

**Features each `Song` uses:**

- `genre` and `mood` — categorical, scored by exact match
- `energy` — numerical (0–1), scored by *closeness* to the user's target
- `acousticness` — numerical, compared against the user's acoustic preference
- (available for later experiments: `valence`, `danceability`, `tempo_bpm`)

**What the `UserProfile` stores:**

- `favorite_genre` — the genre they want most
- `favorite_mood` — the mood they want most
- `target_energy` — their ideal energy level, 0–1 (chill → hype)
- `likes_acoustic` — whether they prefer acoustic tracks

### Example User Profile

The recommender compares every song against a single taste profile:

```python
user_prefs = {
    "favorite_genre": "rock",
    "favorite_mood": "intense",
    "target_energy": 0.9,
    "likes_acoustic": False,
}
```

These three-plus signals reinforce each other, so the system can cleanly tell
"intense rock" apart from "chill lofi": a rock/intense/0.9 profile lifts
*Storm Runner* to the top while pushing *Library Rain* near zero.

### Finalized Algorithm Recipe

The **Scoring Rule** judges one song at a time. Each song earns weighted
points for how well it fits the user:

- **+2.0** if the genre matches
- **+1.0** if the mood matches
- **+1.0 × `energy_score`**, where
  `energy_score = 1 - abs(song.energy - target_energy)`
  — so a song whose energy is *closer* to the target scores higher, rather
  than simply favoring higher-energy songs
- **+0.5** if the acoustic preference matches (`likes_acoustic` vs a high
  `acousticness`)

Genre is weighted highest because it's the strongest single predictor of
taste; mood is a meaningful but secondary match; energy contributes a smooth
"closeness" score instead of an all-or-nothing point.

The **Ranking Rule** then takes over across the whole list: **sort every song
by its total score, highest first, and return the top _k_** (default 5).
Keeping scoring and ranking separate means I can change how one song is judged
without touching how the final list is chosen, and vice versa.

### Data Flow

```text
Input                Process (the loop)                 Output
-----                ------------------                 ------
user_prefs  ──▶  for each song in songs.csv:      ──▶  sort by score desc
(taste           score_song(user_prefs, song)          take top K
 profile)        → (score, reasons)                    → ranked recommendations
```

Input (user prefs) → Process (score every individual song with the Scoring
Rule) → Output (rank the scores and return the top K).

### Potential Biases I Expect

- **Genre over-prioritization.** Because genre is worth +2.0, a perfect
  genre match can outrank a song that matches the user's *mood and energy* but
  sits in a neighboring genre — so great mood-fit songs may be buried.
- **Popular-attribute bias.** Genres/moods that appear more often in the
  catalog have more chances to land in the top K; underrepresented styles are
  structurally disadvantaged.
- **Vibe blindness.** The score can't tell a sad song from a breakup anthem if
  their energy/valence numbers match — it ignores lyrics, vocals, and context.
- **Echo chamber.** Being purely content-based, it only recommends more of
  what the user already likes and never surprises them.

### Optional Extensions Implemented

All four optional challenges are built into the code and shown by
`python -m src.main`:

1. **Advanced features** — `songs.csv` gained `popularity`, `release_decade`,
   `mood_tags`, `instrumentalness`, and `language`, and the scorer awards
   points for decade matches, overlapping mood tags, popularity, and language.
2. **Scoring modes (Strategy pattern)** — `balanced`, `genre-first`,
   `mood-first`, and `energy-focused` modes, selectable via
   `recommend_songs(..., strategy=STRATEGIES["mood-first"])`. See
   `ai_interactions.md`.
3. **Diversity penalty** — `recommend_songs(..., diversity_penalty=0.75)`
   greedily docks points from a song whose artist/genre already appears in the
   picks, so one artist or genre can't dominate the top results.
4. **Formatted table** — output is rendered with `tabulate` (ASCII fallback if
   it isn't installed), including a wrapped "Reasons" column.

---

## Getting Started

### Setup

1. Create a virtual environment (optional but recommended):

   ```bash
   python -m venv .venv
   source .venv/bin/activate      # Mac or Linux
   .venv\Scripts\activate         # Windows

2. Install dependencies

```bash
pip install -r requirements.txt
```

3. Run the app:

```bash
python -m src.main
```

### Running Tests

Run the starter tests with:

```bash
pytest
```

You can add more tests in `tests/test_recommender.py`.

---

## Sample Recommendation Output

Output from `python -m src.main` for the default `pop / happy / 0.8` profile:

```
Loaded songs: 18

User profile: genre=pop, mood=happy, energy=0.8

Top recommendations:

1. Sunrise City - Neon Echo  (score: 3.98)
   Because: genre match: pop (+2.0); mood match: happy (+1.0); energy 0.82 close to target 0.8 (+0.98)

2. Gym Hero - Max Pulse  (score: 2.87)
   Because: genre match: pop (+2.0); energy 0.93 close to target 0.8 (+0.87)

3. Rooftop Lights - Indigo Parade  (score: 1.96)
   Because: mood match: happy (+1.0); energy 0.76 close to target 0.8 (+0.96)

4. Concrete Kingdom - MC Vantage  (score: 1.00)
   Because: energy 0.8 close to target 0.8 (+1.00)

5. Night Drive Loop - Neon Echo  (score: 0.95)
   Because: energy 0.75 close to target 0.8 (+0.95)
```

The top result is *Sunrise City* — the only track that matches genre **and**
mood while sitting right at the target energy — exactly what we'd expect.

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or demo video link here -->

---

## Experiments You Tried

**Weight-shift experiment (energy ×2, genre ÷2).** I temporarily set
`GENRE_WEIGHT = 1.0` and `ENERGY_WEIGHT = 2.0` and re-ran the adversarial
"Conflicted" profile (folk + sad + energy 0.95):

- **Before** (genre 2.0 / energy 1.0): *Paper Boats* (energy 0.30) won by a
  huge margin (3.35 vs. 1.00) — the sad folk match buried the energy request.
- **After** (genre 1.0 / energy 2.0): the loud energy-matched songs
  (*Neon Overdrive*, *Gym Hero*, *Iron Verdict*) all jumped to ~2.0 and filled
  slots 2–5, and *Paper Boats*' lead shrank to 2.70 vs. 2.00.

Verdict: for a "loud + sad" listener this was **more accurate** — the loud
songs they actually asked for finally surfaced. But it made the normal
profiles noisier (energy near-misses started outranking genre matches), so I
**reverted** to genre 2.0 / energy 1.0 as the better all-round default. This
is exactly the genre-over-energy bias documented in the model card.

**Stress-testing different users.** Running five profiles (see
`model_card.md` → Evaluation) showed the system handles clearly-defined tastes
(pop, lofi, rock) very well, but leans on genre/mood whenever a profile's
signals conflict.

---

## Limitations and Risks

Summarize some limitations of your recommender.

Examples:

- It only works on a tiny catalog
- It does not understand lyrics or language
- It might over favor one genre or mood

You will go deeper on this in your model card.

---

## Reflection

Read and complete `model_card.md`:

[**Model Card**](model_card.md)

Write 1 to 2 paragraphs here about what you learned:

- about how recommenders turn data into predictions
- about where bias or unfairness could show up in systems like this



