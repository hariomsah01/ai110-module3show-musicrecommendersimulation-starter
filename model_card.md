# 🎧 Model Card: Music Recommender Simulation

## 1. Model Name  

**VibeFinder 1.0**

---

## 2. Intended Use  

**Goal / Task.** VibeFinder tries to guess which songs a person will like.
You tell it your favorite genre, your favorite mood, and how much energy you
want. It then gives back a short ranked list of songs that best match you, plus
a plain reason for each pick.

**Who it is for.** This is a classroom project for learning how recommenders
work. It is not a real product.

**Assumptions it makes.** It assumes the user can name one favorite genre, one
favorite mood, and one energy level. It also assumes taste can be described by
song attributes alone.

**Intended use:** learning, demos, and experimenting with scoring rules.

**Not intended for:** real listeners, real playlists, or any decision that
matters. It only knows 18 songs and does not learn from real behavior.

---

## 3. How the Model Works  

Think of it like a points game. Every song in the list gets scored against
what you asked for.

- If the song's genre matches yours, it earns 2 points.
- If the song's mood matches yours, it earns 1 point.
- For energy, the closer the song's energy is to your target, the more points
  it earns (up to 1 point). A song right on target gets a full point; a song
  far off gets almost nothing. Closer is better, not just louder.
- If you said you like acoustic music and the song is acoustic (or you don't
  and it isn't), it earns half a point.

Once every song has a total, the model lines them up from highest to lowest
and hands you the top five. The starter code was empty, so I wrote all of the
scoring, the ranking, and the reasons. I also chose to make genre worth the
most points because genre is usually the strongest clue about taste.

---

## 4. Data  

**Size.** The catalog has 18 songs. It started with 10 and I added 8.

**Features per song.** Each song has a genre, a mood, and four numbers between
0 and 1: energy, valence (how positive it sounds), danceability, and
acousticness. It also has a tempo in beats per minute.

**Genres and moods.** After my additions the list covers many styles — pop,
lofi, rock, jazz, ambient, synthwave, indie pop, hip hop, classical, edm,
country, r&b, metal, folk, and reggae — and moods from happy and chill to
sad, aggressive, and nostalgic.

**Limits.** It is still tiny, and most genres appear only once, so there is
little variety to choose from. It also has no lyrics, no language, no artist
popularity, and no release year — so big parts of real musical taste are
simply missing.

---

## 5. Strengths  

The system works best when a user has a clear, consistent taste. For the
**Chill Lofi** and **High-Energy Pop** profiles, every signal pointed the same
way and the top results were exactly the songs I would have picked myself.

It correctly captures the idea that "closer energy is better" — low-energy
profiles pull up calm songs and high-energy profiles pull up loud ones. And
because every recommendation comes with a written reason, the results are easy
to trust and easy to debug. In every test the #1 song made sense once I read
its reasons.

---

## 6. Limitations and Bias 

The biggest weakness I found is that **genre and mood dominate energy**. A
genre match is worth +2.0 and a mood match +1.0, but the energy score can only
ever add between 0 and +1.0. During testing, my adversarial "Conflicted"
profile (folk + sad + energy 0.95) ranked *Paper Boats* first even though that
song sits at energy 0.30 — the exact opposite of what the user asked for. The
+3.0 from matching genre and mood simply buried the energy mismatch, so the
system effectively **ignores a user's stated energy whenever a categorical
match is available**. This also creates a filter bubble: because scoring is
purely content-based, users only ever see more of the genre they already
named, and any genre/mood that appears rarely in the 18-song catalog (most
genres appear only once) is structurally unlikely to reach the top of a list
it doesn't perfectly match. The model also has no notion of lyrics, vocals, or
context, so it cannot tell a sad song from an angry one when their numbers are
similar.

---

## 7. Evaluation  

I tested five profiles via `python -m src.main`: three normal ones
(**High-Energy Pop**, **Chill Lofi**, **Deep Intense Rock**) and two
adversarial ones (**Conflicted** = loud + sad, and **Impossible combo** =
a genre/mood pair that never appears together in the catalog). For each I
looked at whether the top 5 respected all three signals — genre, mood, and
energy — or leaned too hard on one.

### Terminal output

```
===== High-Energy Pop =====
Profile: genre=pop, mood=happy, energy=0.9
1. Sunrise City - Neon Echo  (score: 3.92)  [genre+mood+energy 0.82]
2. Gym Hero - Max Pulse  (score: 2.97)      [genre+energy 0.93]
3. Rooftop Lights - Indigo Parade (score: 1.86) [mood+energy 0.76]

===== Chill Lofi =====
Profile: genre=lofi, mood=chill, energy=0.3, likes_acoustic=True
1. Library Rain - Paper Lanterns  (score: 4.45) [genre+mood+energy+acoustic]
2. Midnight Coding - LoRoom  (score: 4.38)      [genre+mood+energy+acoustic]
3. Focus Flow - LoRoom  (score: 3.40)           [genre+energy+acoustic]

===== Deep Intense Rock =====
Profile: genre=rock, mood=intense, energy=0.95
1. Storm Runner - Voltline  (score: 3.96)   [genre+mood+energy 0.91]
2. Gym Hero - Max Pulse  (score: 1.98)      [mood+energy 0.93]
3. Neon Overdrive - Pulsewave  (score: 1.00) [energy only]

===== Conflicted (loud + sad) =====
Profile: genre=folk, mood=sad, energy=0.95
1. Paper Boats - Ellie Wren  (score: 3.35)  [genre+mood, but energy 0.30!]
2. Neon Overdrive - Pulsewave  (score: 1.00) [energy only]

===== Impossible combo =====
Profile: genre=reggae, mood=aggressive, energy=0.2
1. Island Time - Sunny Roots  (score: 2.60)  [genre only]
2. Iron Verdict - Blacksteel  (score: 1.22)  [mood only]
```

### What surprised me

For the **Conflicted** profile I expected a loud song, but the #1 result was
a quiet sad folk track. The genre + mood match (+3.0) beat the energy penalty,
which is how I discovered that energy is the weakest of my three signals.

### Profile comparisons (plain language)

- **High-Energy Pop vs. Chill Lofi:** these are near-opposites and the system
  handled them cleanly — the pop profile pulls up bright, fast pop songs while
  the lofi profile shifts entirely to slow, acoustic, low-energy tracks. This
  makes sense: every signal (genre, mood, energy, acousticness) points the
  same direction for each, so there's no tug-of-war.
- **High-Energy Pop vs. Deep Intense Rock:** both want high energy, so *Gym
  Hero* (a loud pop/intense song) shows up near the top of **both** lists. The
  difference is which song wins #1 — *Sunrise City* for pop, *Storm Runner*
  for rock — decided purely by the genre match. This is the "Gym Hero keeps
  showing up" effect: any high-energy song is a decent partial match for
  anyone who asks for high energy, so it appears on many lists even when the
  genre is wrong.
- **Deep Intense Rock vs. Conflicted:** both target energy ~0.95, but the
  rock profile's top result is genuinely loud (*Storm Runner*, 0.91) while the
  conflicted profile's top result is quiet (*Paper Boats*, 0.30). The only
  difference is that "sad" matches a low-energy song, and that mood point was
  enough to override the energy request — the clearest sign that my weights
  let categorical matches overrule the numbers.
- **Impossible combo:** with no song matching both reggae AND aggressive, the
  system split the difference — genre alone lifted a reggae song to #1 and
  mood alone lifted a metal song to #2 — which is reasonable fallback
  behavior for a request the catalog can't actually satisfy.

No numeric accuracy metrics were computed; evaluation was qualitative.

---

## 8. Future Work (Ideas for Improvement)

1. **Rebalance energy against genre.** Right now genre can bury a bad energy
   match. I'd cap or scale the categorical points so a big energy miss can pull
   a song back down, or let the user choose how much energy should matter.
2. **Add a diversity rule.** I'd stop the top 5 from being crowded by one
   artist or genre, so the list feels more like a real playlist.
3. **Grow the catalog and add richer features.** More songs per genre would
   give real variety, and features like popularity, release decade, or multiple
   mood tags would let it match more complex tastes.

---

## 9. Personal Reflection  

**Biggest learning moment.** The adversarial "loud + sad" test was the moment
it clicked. Watching a quiet folk song win a list for someone who asked for
high energy showed me that a recommender is really just the *weights* you
choose — the math is simple, but the weights quietly decide everything.

**How AI helped, and when I checked it.** The AI was fastest at writing the
CSV loader, the scoring loop, and the terminal formatting, and at suggesting
edge-case profiles I wouldn't have thought of. I had to double-check it on the
things that actually mattered: it originally imported the recommender in a way
that crashed under `python -m src.main`, and I made sure the energy math and
the weights matched the recipe I designed instead of blindly trusting the
generated numbers. I treated its output as a draft to verify, not an answer.

**What surprised me.** I was surprised how much a handful of if-statements and
a sort can "feel" like a real recommendation. There's no machine learning
here, yet the reasons it prints make it feel like it understands you. It made
me realize how much of a recommendation is just clear rules plus a good
explanation.

**What I'd try next.** I'd add the diversity rule and let users switch between
scoring modes (genre-first vs. energy-first), then test whether the lists feel
more varied and fair.
