# TakeMeter — Planning Document

## Community

**r/nba** — the primary subreddit for NBA basketball discussion with ~8M members.

This community is an ideal fit for a classification task because its discourse spans an unusually wide quality range: the same thread can contain data-driven breakdowns of a player's efficiency splits, pure emotional reactions to a buzzer-beater, and confident opinions stated without any evidence. NBA fans themselves regularly debate whether a claim is a "hot take" or "actual analysis," making the distinction culturally meaningful within the community — not just an artificial label imposed from outside. Text is long enough (most top-level posts are 2–10 sentences) to contain enough signal for a model to learn from.

---

## Labels

Three labels, mutually exclusive:

### `analysis`
A post that makes a structured argument backed by statistics, historical comparisons, tactical observations, or other verifiable evidence. The evidence is specific and could be independently checked; removing it would substantially weaken the argument.

**Examples:**
- "The Celtics' defensive rating drops 8.2 points per 100 possessions in 4th quarters of games within 5 points — that's not a coach problem, that's their bench lineup. Check the lineup data on PBP Stats."
- "Wembanyama's rookie blocks-per-36 (3.6) is higher than Hakeem's (3.1), KAT's (2.4), and Robinson's (3.3). Statistically he's having the best shot-blocking rookie season since Shaq. That's not hype, that's the data."

### `hot_take`
A bold, confident opinion stated without supporting evidence or with only decorative evidence. The claim might be correct, but the post asserts rather than argues. Often uses absolute language ("always," "never," "already the GOAT") without citing specific data.

**Examples:**
- "Luka is already better than Dirk ever was and it's not even close. Just accept it."
- "The Lakers will never win another championship with LeBron. He's too old and his supporting cast is cooked. Stop pretending otherwise."

### `reaction`
An immediate emotional response to a specific game event, trade announcement, or breaking news. Little to no argument — the post expresses a feeling or surprise in the moment. Context is usually tied to something that just happened.

**Examples:**
- "I CANNOT believe they just traded Kyrie. What is going on with this league??"
- "That Kawhi shot just ended a whole franchise's season. I'm still shaking. This sport is insane."

---

## Hard Edge Cases

**The one-stat hot take** — a post that cites a single statistic to support a bold opinion:

> "LeBron's playoff win rate against top-seeded opponents is below .500. He's overrated and people need to stop acting like he's infallible."

This post cites a specific, verifiable stat — but the stat is cherry-picked for rhetorical effect, and the argument would still be made without it. The framing is accusatory, not exploratory.

**Decision rule:** If the evidence is specific, verifiable, AND forms the logical core of the argument (i.e., the post is reasoning from evidence to conclusion), label it `analysis`. If the evidence is decorative — one stat selected to make an assertion sound credible, without building a real argument — label it `hot_take`. The test: would removing the stat change the post's conclusion? If yes, it's analysis. If no (the opinion was already decided and the stat is support-shopping), it's a hot take.

A secondary edge case is the **hot-take-with-context reaction** — a post that reacts emotionally to a game but also makes a bold claim:

> "This loss proved the Knicks are frauds. I knew they couldn't close."

**Decision rule:** If the post's primary purpose is expressing a feeling triggered by a specific, recent event, label it `reaction`. If the post's primary purpose is asserting an opinion that stands independent of the event (the event is evidence for a claim, not the trigger for a feeling), label it `hot_take`.

---

## Data Collection Plan

**Source:** Reddit posts and comments from r/nba, collected manually or via Reddit's public API (Pushshift archive or direct API with read-only access).

**Target size:** 210 examples — 70 per label.

**Collection strategy:**
- `analysis`: search for posts that cite stats, compare players across eras, or break down film/tactical observations. Game-thread top-level analytical comments and weekly discussion threads ("Breakdown of X's performance") are good sources.
- `hot_take`: "Hot takes" megathread posts, post-game threads where users make sweeping claims, and any post starting with "Unpopular opinion:" or "Change my mind."
- `reaction`: Game threads (in-game comments), trade deadline reaction posts, and breaking news comment sections.

**If a label is underrepresented after 200 examples:** Actively search for that label type using keyword filters (e.g., "stat" or "per 100" for analysis; "game thread" for reaction) rather than sampling uniformly. Document any active oversampling in the dataset CSV.

**Format:** Each row in the CSV contains: `text`, `label`, `source_url` (optional), `annotator_notes` (optional).

---

## Evaluation Metrics

**Primary metrics:**
- **Macro F1** — the average F1 across all three classes, weighted equally. This is the primary metric because it penalizes the model equally for failing on any class, regardless of class frequency. Accuracy alone would be misleading if one label dominates the dataset.
- **Per-class F1** — separate F1 for `analysis`, `hot_take`, and `reaction`. This tells us which distinctions the model is learning and where it's failing. The `hot_take` vs `analysis` boundary is the hardest, so we expect the lowest F1 there.

**Secondary metrics:**
- **Confusion matrix** — visualizes which labels are being swapped. Specifically, we want to see whether the model confuses `hot_take` with `analysis` (expected) vs. `reaction` with `hot_take` (a worse failure, since these are more conceptually distinct).
- **Per-class precision and recall** — if precision is low, the model is over-assigning a label. If recall is low, it's missing real examples of a label.

**Why not just accuracy?** With three roughly balanced classes (70 examples each), a model that always predicts `hot_take` would get ~33% accuracy — which looks bad but hides that it learned nothing. Macro F1 exposes this.

---

## Definition of Success

A classifier is "good enough for deployment" in a community tool (e.g., a browser extension that tags r/nba posts) if:

- **Macro F1 ≥ 0.70** — the model is meaningfully better than random on all three classes
- **No per-class F1 below 0.60** — the model hasn't completely given up on any label
- **`hot_take` and `analysis` F1 both ≥ 0.65** — the hardest boundary is handled acceptably

These thresholds were chosen because:
- Below macro F1 0.70, users would encounter wrong labels often enough to distrust the tool
- A single class below 0.60 means the tool is useless for that label type, breaking the taxonomy's value
- The `hot_take`/`analysis` threshold is set lower than the overall bar because this boundary is genuinely hard, even for humans

**Acceptable but worth documenting:** Macro F1 between 0.65–0.70, with clear error patterns that a better prompt or more data could fix. This would be reported as "promising but not yet deployment-ready."

---

## AI Tool Plan

### 1. Label stress-testing (before annotation)

Before labeling 200 examples, I will give Claude my three label definitions and the one-stat hot take edge case, and ask it to generate 10 posts that sit at the boundary between `hot_take` and `analysis`. If it produces posts I can't classify cleanly using my decision rule, that's a signal to tighten the definitions before annotating. I'll refine the decision rule until I can classify every generated boundary case in under 5 seconds.

**Prompt template I'll use:**
> "Here are three labels for r/nba posts: [paste definitions]. Generate 10 posts that deliberately sit at the boundary between hot_take and analysis — posts where a reader could reasonably argue for either label."

### 2. Annotation assistance

I will use an LLM (Claude) to pre-label the first 50 examples before reviewing each one myself. This speeds up the process and surfaces disagreements that reveal annotation ambiguity. Every pre-labeled example will be marked with `annotator: llm_assisted` in the CSV, and I will personally review and accept/override each label. The final label is always mine.

I will not use LLM pre-labeling as a shortcut — I'll read every example before accepting the label.

### 3. Failure analysis

After evaluation, I will export the list of misclassified examples and their predicted labels, then ask Claude:
> "Here are posts my classifier got wrong. Each one shows the true label and the predicted label. What patterns do you see in the mistakes? Are there specific phrasings or post structures that the model is systematically misclassifying?"

I will verify any claimed pattern myself by reading the raw examples — I won't accept an AI summary of failures without checking it against the actual data.
