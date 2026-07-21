# AI Interactions Log

> **Stretch features only.** Only fill in the sections that apply to stretch features you attempted. If you did not attempt a stretch feature, leave its section blank or delete it. This file is not required for the core project.

---

## Agentic Workflow (SF8)

> Document your experience using an AI agent (e.g., Cursor Agent, Claude, Copilot) to make multi-step changes autonomously.

**What task did you give the agent?**

Add 5+ advanced song features to the dataset and make the recommender score
them (Challenge 1). This was multi-step: it had to touch `data/songs.csv`, the
`Song` dataclass, the CSV loader, and the scoring logic all at once.

**Prompts used:**

> "Add five new columns to data/songs.csv — popularity (0–100),
> release_decade, mood_tags (pipe-separated, e.g. `calm|study`),
> instrumentalness (0–1), and language — and fill in realistic values for all
> 18 songs. Then update the Song dataclass, load_songs, and score_song in
> src/recommender.py so these features are scored. Give the new dataclass
> fields default values so the existing tests still pass, and only add points
> for a feature when the user profile actually asks for it."

**What did the agent generate or change?**

- `data/songs.csv`: 5 new columns + values for all 18 songs
- `src/recommender.py`: new `Song` fields (with defaults), `INT_FIELDS` /
  `FLOAT_FIELDS` parsing in `load_songs`, and new guarded scoring blocks for
  decade, mood tags, popularity, and language
- Reasons strings so each new feature explains itself in the output

**What did you verify or fix manually?**

- Confirmed the new dataclass fields had **defaults** so `tests/test_recommender.py`
  (which builds `Song` with only the original 10 fields) still passed — ran
  `pytest` to be sure (2 passed).
- Checked that `mood_tags` used `|` and not commas, since commas would break
  the CSV.
- Verified the advanced features only score when the profile includes the key
  (e.g. `target_decade`), so the core profiles behave the same as before.

---

## Design Pattern (SF10)

> Document how AI helped you choose or implement a design pattern.

**Which design pattern did you use?**

The **Strategy pattern** — to support switchable scoring modes (Challenge 2):
`balanced`, `genre-first`, `mood-first`, and `energy-focused`.

**How did AI help you brainstorm or implement it?**

I asked how to let a user switch ranking strategies without duplicating the
scoring code or writing a big `if/elif` on the mode name. The AI suggested the
Strategy pattern: one base class holding the scoring algorithm, with
subclasses that only change a weight table. That keeps the *how we score* in
one place and makes each *mode* a tiny, swappable object.

**How does the pattern appear in your final code?**

In `src/recommender.py`: a base `ScoringStrategy.score()` method contains the
single scoring algorithm, and `GenreFirst`, `MoodFirst`, and `EnergyFocused`
subclass it, overriding only `weights`. A `STRATEGIES` registry maps mode names
to instances, and `recommend_songs(..., strategy=STRATEGIES["mood-first"])`
lets `main.py` switch modes with one argument.
