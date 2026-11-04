# Contest sync

Every rated contest I give on LeetCode, Codeforces and CodeChef is added to the [contest archive](../contests/) automatically. The scores sync themselves; the editorials don't.

## What syncs

| Platform | Source | What it records | My code |
|---|---|---|---|
| LeetCode | Public GraphQL and the contest info endpoint | Rank, rating, solved count, problem list, and whether each problem was accepted during the contest or later | Copied verbatim from my LeetHub repository |
| Codeforces | [Official API](https://codeforces.com/apiHelp) | Rank, rating change, problem list, time and wrong attempts per problem, upsolves | Added by hand |
| CodeChef | Rating history embedded in my public profile page (CodeChef has no public API) | Rank and rating | Added by hand; problem list needs import |

No login or session cookie is used anywhere.

## Rules the sync follows

- **Nothing is published while a contest is running.** A contest is only written after its end time.
- **Statements are linked, never copied.** Draft editorials link to the official problem page.
- **Hand-written text is never overwritten.** Contest READMEs are created once; later runs only rewrite the block between the `CONTEST-SYNC` markers. Existing problem folders (like `Q2-last-visited-cell`) are reused, never duplicated.
- **Drafts stay drafts.** When my code arrives, the sync creates `Q<n>-<slug>/submission.<ext>` and a draft `README.md`, but no `metadata.yaml`. The problem only joins the featured index and the publication pipeline after the editorial is written (Intuition → Brute Force → Bottleneck → Optimization → Proof) and `solution.py`, `tests.py` and `metadata.yaml` are added.

A synced accepted submission is not an upsolve. Every contest README starts with **Upsolve pending**.

## How it runs

`.github/workflows/contest-sync.yml` runs daily (and on demand), executes `scripts/contest_sync/sync.py`, runs `scripts/validate_repo.py`, and opens or updates a pull request on the `contest-sync` branch. Nothing reaches the site until that pull request is merged. If one platform fails (site down, page layout changed), the others still sync and the run is marked failed.

Offline tests: `python3 scripts/contest_sync/tests.py -v` (also run by `validate_repo.py`).

## One-time setup

1. **Settings → Secrets and variables → Actions → Variables**: add `LEETCODE_HANDLE`, `CODEFORCES_HANDLE`, `CODECHEF_HANDLE`. Leave one out to skip that platform.
2. **Settings → Actions → General → Workflow permissions**: allow GitHub Actions to create and approve pull requests.
3. **LeetCode code (optional)**: install the LeetHub extension, point it at a repository, and set the variable `LEETHUB_REPO` (for example `KatalKavya96/leetcode-solutions`). If that repository is private, add a fine-grained read-only token as the secret `LEETHUB_TOKEN`.
4. **Actions → Contest sync → Run workflow** once to backfill.
