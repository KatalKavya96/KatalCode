#!/usr/bin/env python3
"""Sync my public contest results from LeetCode, Codeforces and CodeChef into the archive.

    python3 scripts/contest_sync/sync.py                     every platform whose handle is set
    python3 scripts/contest_sync/sync.py --only codeforces
    python3 scripts/contest_sync/sync.py --fixtures DIR      offline: DIR/<platform>.json snapshots

Handles come from the environment (repository variables in the workflow):
LEETCODE_HANDLE, CODEFORCES_HANDLE, CODECHEF_HANDLE. LEETHUB_DIR optionally points at a checkout
of the repository the LeetHub extension pushes to; my LeetCode code is copied from there verbatim.

Only public data is read. No login, no session cookie.

What it writes:
  data/contest-history.json                   accumulated state for all platforms
  contests/<platform>/.../<contest>/README.md  created once; afterwards only the block between
                                               the CONTEST-SYNC markers is rewritten
  contests/.../<contest>/Q<n>-<slug>/          created when my code exists: submission.<ext>
                                               (verbatim) and a draft editorial README.md
  generated tables in the platform index READMEs

Rules it enforces:
  * a contest is only written after it has ended, so no solution is published while it is live;
  * problem statements are linked, never copied;
  * existing editorials, solutions and hand-written text are never overwritten;
  * draft problem folders get no metadata.yaml, so they stay out of the featured index and the
    publication pipeline until the editorial is actually written.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
START = "<!-- CONTEST-SYNC:START (generated, edit outside this block) -->"
END = "<!-- CONTEST-SYNC:END -->"
IST = timezone(timedelta(hours=5, minutes=30))
LANGS = {".py": "Python", ".java": "Java", ".cpp": "C++", ".cc": "C++", ".c": "C", ".js": "JavaScript",
         ".ts": "TypeScript", ".go": "Go", ".kt": "Kotlin", ".rs": "Rust"}
UA = {"User-Agent": "KatalCode-contest-sync"}
PLATFORM_NAMES = {"leetcode": "LeetCode", "codeforces": "Codeforces", "codechef": "CodeChef"}


# ---------------------------------------------------------------- helpers

def slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", str(text).lower()).strip("-")


def day(epoch: int) -> str:
    d = datetime.fromtimestamp(epoch, IST)
    return f"{d.strftime('%B')} {d.day}, {d.year}"


def clock(seconds) -> str:
    if seconds is None:
        return "—"
    seconds = int(seconds)
    return f"{seconds // 60}:{seconds % 60:02d}"


def signed(n) -> str:
    return "—" if n is None else (f"+{n}" if n > 0 else str(n))


def num(n) -> str:
    return "—" if n is None else f"{int(n):,}"


def http_json(url: str, data: dict | None = None, headers: dict | None = None):
    body = json.dumps(data).encode() if data is not None else None
    req = urllib.request.Request(url, data=body, headers={**UA, **(headers or {})})
    if body:
        req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, timeout=30) as res:
        return json.load(res)


def http_text(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (KatalCode-contest-sync)"})
    with urllib.request.urlopen(req, timeout=30) as res:
        return res.read().decode("utf-8", "replace")


# A normalised contest:
#   {key, dir, title, links: [[text, url]], start, end, rank, solved, total, finish, rating, change,
#    problems: [{label, title, url, points, status, slug}]}
# `dir` is relative to ROOT. `slug` names the problem folder (Q<n>-<slug> / <index>-<slug>).


# ---------------------------------------------------------------- LeetCode

LC_SECONDS = 90 * 60
LC_QUERY = """query ($username: String!) {
  userContestRanking(username: $username) { attendedContestsCount rating globalRanking topPercentage }
  userContestRankingHistory(username: $username) {
    attended rating ranking problemsSolved totalProblems finishTimeInSeconds
    contest { title startTime }
  }
  recentAcSubmissionList(username: $username, limit: 20) { id title titleSlug timestamp lang }
}"""
LC_HEADERS = {"Referer": "https://leetcode.com"}


def lc_fetch(handle: str, prev: dict) -> dict:
    body = http_json("https://leetcode.com/graphql", {"query": LC_QUERY, "variables": {"username": handle}}, LC_HEADERS)
    if body.get("errors"):
        raise RuntimeError(f"LeetCode GraphQL: {body['errors']}")
    d = body["data"]
    if d.get("userContestRankingHistory") is None:
        raise RuntimeError(f'LeetCode: no contest data for "{handle}"')
    known = {c["key"] for c in prev.get("contests", []) if c["problems"]}
    questions = {}
    for h in d["userContestRankingHistory"]:
        slug = slugify(h["contest"]["title"])
        if not h["attended"] or slug in known:
            continue
        try:
            info = http_json(f"https://leetcode.com/contest/api/info/{slug}/", headers=LC_HEADERS)
            questions[slug] = [{"title": q["title"], "slug": q["title_slug"], "credit": q.get("credit")}
                               for q in info.get("questions", [])]
        except Exception:  # best effort: the README then says the problem list needs import
            pass
    return {"username": handle, "ranking": d.get("userContestRanking"), "history": d["userContestRankingHistory"],
            "recentAc": d.get("recentAcSubmissionList") or [], "questions": questions}


def lc_build(prev: dict, snap: dict) -> dict:
    accepted = dict(prev.get("accepted", {}))
    for s in snap["recentAc"]:
        accepted[str(s["id"])] = {"slug": s["titleSlug"], "timestamp": int(s["timestamp"])}
    # The list holds at most 20 items. If the first fetch was full, older accepts are invisible.
    since = prev.get("acceptedSince")
    if since is None:
        since = min(int(s["timestamp"]) for s in snap["recentAc"]) if len(snap["recentAc"]) >= 20 else 0
    old_q = {c["key"]: c.get("rawQuestions", []) for c in prev.get("contests", [])}

    def status(q_slug, start):
        hits = [s["timestamp"] for s in accepted.values() if s["slug"] == q_slug]
        if hits:
            first = min(hits)
            if start <= first <= start + LC_SECONDS:
                return f"Accepted in contest ({clock(first - start)})"
            if first > start + LC_SECONDS:
                return f"Upsolved {day(first)}"
        return "Unknown (before sync history)" if start < since else "Not accepted yet"

    contests, last = [], 1500
    for h in sorted((h for h in snap["history"] if h["attended"]), key=lambda h: h["contest"]["startTime"]):
        title, start = h["contest"]["title"], h["contest"]["startTime"]
        key = slugify(title)
        m = re.match(r"(weekly|biweekly)-contest-(\d+)$", key)
        directory = f"contests/leetcode/{m.group(1)}/{m.group(2)}" if m else f"contests/leetcode/other/{key}"
        rating = round(h["rating"])
        qs = snap["questions"].get(key) or old_q.get(key) or []
        contests.append({
            "key": key, "dir": directory, "title": f"LeetCode {title}",
            "links": [["Contest", f"https://leetcode.com/contest/{key}/"], ["Ranking", f"https://leetcode.com/contest/{key}/ranking/"]],
            "start": start, "end": start + LC_SECONDS,
            "rank": h["ranking"], "solved": h["problemsSolved"], "total": h["totalProblems"],
            "finish": clock(h["finishTimeInSeconds"]) if h["finishTimeInSeconds"] else None,
            "rating": rating, "change": rating - last, "rawQuestions": qs,
            "problems": [{"label": f"Q{i + 1}", "title": q["title"], "url": f"https://leetcode.com/problems/{q['slug']}/",
                          "points": q.get("credit"), "status": status(q["slug"], start), "slug": q["slug"]}
                         for i, q in enumerate(qs)],
        })
        last = rating
    r = snap.get("ranking")
    summary = (f"**Rating {round(r['rating'])}** · {r['attendedContestsCount']} contests · global rank "
               f"{num(r['globalRanking'])} · top {r['topPercentage']}% · [profile](https://leetcode.com/u/{snap['username']}/)") if r else None
    return {"state": {"username": snap["username"], "acceptedSince": since, "accepted": accepted, "contests": contests},
            "summary": summary, "contests": contests}


def leethub_code(leethub: Path | None) -> dict[str, list[Path]]:
    """LeetHub writes one folder per problem: "<number>-<slug>" (newer) or "<slug>" (older)."""
    found: dict[str, list[Path]] = {}
    if not leethub or not leethub.is_dir():
        return found
    for folder in leethub.iterdir():
        if folder.is_dir() and not folder.name.startswith("."):
            files = [f for f in folder.iterdir() if f.suffix in LANGS]
            if files:
                found[re.sub(r"^\d+-", "", folder.name)] = sorted(files)
    return found


# ---------------------------------------------------------------- Codeforces

def cf_call(method: str, **params):
    body = http_json(f"https://codeforces.com/api/{method}?{urllib.parse.urlencode(params)}")
    time.sleep(2.1)  # Codeforces allows about one call every two seconds
    if body.get("status") != "OK":
        raise RuntimeError(f"Codeforces {method}: {body.get('comment')}")
    return body["result"]


def cf_fetch(handle: str, prev: dict) -> dict:
    info = cf_call("user.info", handles=handle)[0]
    rating = cf_call("user.rating", handle=handle)
    subs = cf_call("user.status", handle=handle)
    known = {c["contestId"] for c in prev.get("contests", []) if c.get("raw")}
    standings = {}
    for r in rating:
        if r["contestId"] in known:
            continue
        s = cf_call("contest.standings", contestId=r["contestId"], handles=handle, showUnofficial="false")
        row = s["rows"][0] if s["rows"] else None
        standings[str(r["contestId"])] = {
            "contest": {k: s["contest"].get(k) for k in ("id", "name", "startTimeSeconds", "durationSeconds")},
            "problems": [{"index": p["index"], "name": p["name"], "points": p.get("points")} for p in s["problems"]],
            "row": row and {"rank": row["rank"], "results": row["problemResults"]},
        }
    return {"handle": handle, "info": {k: info.get(k) for k in ("rating", "maxRating", "rank")}, "rating": rating,
            "upsolves": [{"contestId": s["problem"].get("contestId"), "index": s["problem"]["index"], "time": s["creationTimeSeconds"]}
                         for s in subs if s.get("verdict") == "OK" and s["author"]["participantType"] != "CONTESTANT"],
            "standings": standings}


def cf_build(prev: dict, snap: dict) -> dict:
    old = {c["contestId"]: c.get("raw") for c in prev.get("contests", [])}
    upsolved: dict[str, int] = {}
    for u in snap["upsolves"]:
        k = f"{u['contestId']}{u['index']}"
        upsolved[k] = min(upsolved.get(k, u["time"]), u["time"])
    contests = []
    for r in snap["rating"]:
        cid = r["contestId"]
        raw = snap["standings"].get(str(cid)) or old.get(cid)
        start = (raw or {}).get("contest", {}).get("startTimeSeconds") or r["ratingUpdateTimeSeconds"]
        duration = (raw or {}).get("contest", {}).get("durationSeconds") or 0
        results = ((raw or {}).get("row") or {}).get("results", [])
        problems = []
        for i, p in enumerate((raw or {}).get("problems", [])):
            res = results[i] if i < len(results) else {}
            wrong = res.get("rejectedAttemptCount") or 0
            key = f"{cid}{p['index']}"
            if (res.get("points") or 0) > 0:
                st = f"Accepted in contest ({clock(res.get('bestSubmissionTimeSeconds'))}{f', {wrong} wrong' if wrong else ''})"
            elif key in upsolved:
                st = f"Upsolved {day(upsolved[key])}"
            else:
                st = f"Not solved ({wrong} wrong)" if wrong else "Not solved yet"
            problems.append({"label": p["index"], "title": p["name"], "url": f"https://codeforces.com/contest/{cid}/problem/{p['index']}",
                             "points": p.get("points"), "status": st, "slug": slugify(p["name"])})
        solved = [x for x in results if (x.get("points") or 0) > 0]
        contests.append({
            "contestId": cid, "key": str(cid), "dir": f"contests/codeforces/{cid}", "title": r["contestName"],
            "links": [["Contest", f"https://codeforces.com/contest/{cid}"],
                      ["My submissions", f"https://codeforces.com/submissions/{snap['handle']}/contest/{cid}"]],
            "start": start, "end": start + duration, "rank": r["rank"],
            "solved": len(solved) if raw else None, "total": len(raw["problems"]) if raw else None,
            "finish": clock(max(x["bestSubmissionTimeSeconds"] for x in solved)) if solved else None,
            "rating": r["newRating"], "change": r["newRating"] - r["oldRating"], "raw": raw, "problems": problems,
        })
    i = snap["info"]
    summary = (f"**Rating {i.get('rating') or 'unrated'}** ({i.get('rank') or '—'}) · max {i.get('maxRating') or '—'} · "
               f"{len(snap['rating'])} rated contests · [profile](https://codeforces.com/profile/{snap['handle']})")
    return {"state": {"handle": snap["handle"], "contests": contests}, "summary": summary, "contests": contests}


# ---------------------------------------------------------------- CodeChef
# No public API for user data exists, so this reads the rating history that the public profile
# page embeds as `var all_rating = [...]`. If CodeChef changes the page it fails loudly.

def cc_fetch(handle: str, prev: dict) -> dict:
    return {"handle": handle, **cc_parse(http_text(f"https://www.codechef.com/users/{urllib.parse.quote(handle)}"))}


def cc_parse(html: str) -> dict:
    m = re.search(r"var\s+all_rating\s*=\s*(\[.*?\]);", html, re.S)
    if not m:
        raise RuntimeError("CodeChef: rating history not found on the profile page (page layout changed?)")
    rating = re.search(r'<div class="rating-number">\s*(\d+)', html)
    stars = re.search(r'<span class="rating">\s*([^<]+)<', html)
    return {"history": json.loads(m.group(1)), "rating": int(rating.group(1)) if rating else None,
            "stars": stars.group(1).strip() if stars else None}


def cc_build(prev: dict, snap: dict) -> dict:
    def epoch(s: str) -> int:  # end_date is IST, e.g. "2026-10-29 22:00:00"
        return int(datetime.strptime(s, "%Y-%m-%d %H:%M:%S").replace(tzinfo=IST).timestamp())

    contests, last = [], None
    for h in sorted(snap["history"], key=lambda h: epoch(h["end_date"])):
        rating, end = int(h["rating"]), epoch(h["end_date"])
        contests.append({
            "key": h["code"], "dir": f"contests/codechef/{h['code']}", "title": f"CodeChef {h['name']}",
            "links": [["Contest", f"https://www.codechef.com/{h['code']}"],
                      ["My submissions", f"https://www.codechef.com/{h['code']}/status?usernames={snap['handle']}"]],
            "start": end, "end": end, "rank": int(h["rank"]), "solved": None, "total": None, "finish": None,
            "rating": rating, "change": None if last is None else rating - last, "problems": [],
        })
        last = rating
    stars = f" ({snap['stars']})" if snap.get("stars") else ""
    summary = (f"**Rating {snap.get('rating') or last or '—'}**{stars}"
               f" · {len(contests)} rated contests · [profile](https://www.codechef.com/users/{snap['handle']})")
    return {"state": {"handle": snap["handle"], "contests": contests}, "summary": summary, "contests": contests}


PLATFORMS = {"leetcode": (lc_fetch, lc_build), "codeforces": (cf_fetch, cf_build), "codechef": (cc_fetch, cc_build)}


# ---------------------------------------------------------------- writing

def problem_folder(contest_dir: Path, p: dict) -> Path:
    """Reuse an existing folder for this problem (e.g. Q2-last-visited-cell) instead of duplicating it."""
    if contest_dir.is_dir():
        for child in sorted(contest_dir.iterdir()):
            if child.is_dir() and child.name.lower().startswith(f"{p['label'].lower()}-"):
                return child
    return contest_dir / f"{p['label']}-{p['slug']}"


def write_code(contest_dir: Path, p: dict, files: list[Path]) -> list[str]:
    folder = problem_folder(contest_dir, p)
    folder.mkdir(parents=True, exist_ok=True)
    written = []
    for f in files:
        dest = folder / f"submission{f.suffix}"
        if not dest.exists() or dest.read_bytes() != f.read_bytes():
            shutil.copyfile(f, dest)
            written.append(dest.relative_to(ROOT).as_posix())
    readme = folder / "README.md"
    if not readme.exists():
        readme.write_text(draft_editorial(p, folder), encoding="utf-8")
    return written


def draft_editorial(p: dict, folder: Path) -> str:
    subs = sorted(folder.glob("submission.*"))
    code_links = " · ".join(f"[My submission ({LANGS.get(s.suffix, s.suffix)})](./{s.name})" for s in subs)
    return f"""# {p['label']} — {p['title']}

> **Draft.** My contest code is here; the editorial is written during the upsolve.

[Problem statement]({p['url']}) · {code_links}

## Problem overview

Explain the task briefly in original words (do not copy the statement). State the input, required output, and decisive constraints.

## What I did in the contest

My first idea, where time went, wrong attempts, verbatim.

## Intuition

## Brute-force solution

## Why brute force may fail

## Key observation

## Optimized approach

## Detailed dry run

## Correctness proof

## Complexity

## Edge cases and common mistakes

## Key takeaways

<!-- When this is complete: add solution.py, tests.py and metadata.yaml (see templates/), then run
     python3 scripts/update_indexes.py and python3 scripts/validate_repo.py. -->
"""


def render_block(c: dict, contest_dir: Path) -> str:
    lines = [START, "", " · ".join([f"Held on {day(c['start'])}", *(f"[{t}]({u})" for t, u in c["links"])]), "",
             "| Rank | Solved | Finish time | Rating after | Change |", "|---|---|---|---|---|",
             f"| {num(c['rank'])} | {c['solved'] if c['solved'] is not None else '—'} / {c['total'] if c['total'] is not None else '—'} | "
             f"{c['finish'] or '—'} | {c['rating'] if c['rating'] is not None else '—'} | {signed(c['change'])} |", ""]
    if c["problems"]:
        lines += ["| # | Problem | Points | Status | Here |", "|---|---|---|---|---|"]
        for p in c["problems"]:
            folder = problem_folder(contest_dir, p)
            if (folder / "metadata.yaml").exists():
                here = f"[Editorial](./{folder.name}/)"
            elif (folder / "README.md").exists():
                here = f"[Draft](./{folder.name}/)"
            else:
                here = "—"
            lines.append(f"| {p['label']} | [{p['title']}]({p['url']}) | {p['points'] if p['points'] is not None else '—'} | {p['status']} | {here} |")
    else:
        lines.append("Problem list: **needs import** (not available from the platform's public data).")
    lines += ["", END]
    return "\n".join(lines)


def replace_block(text: str, block: str) -> str:
    if START in text and END in text:
        before, rest = text.split(START, 1)
        return before + block + rest.split(END, 1)[1]
    # Hand-written README without markers: insert the block under the title, touch nothing else.
    head, sep, tail = text.partition("\n")
    return f"{head}\n\n{block}\n{sep}{tail}"


def new_contest_readme(c: dict, contest_dir: Path) -> str:
    return f"""# {c['title']}

{render_block(c, contest_dir)}

> **Upsolve pending.** The numbers above sync automatically. Every problem I didn't solve, or solved slowly or with wrong attempts, gets an editorial before this contest counts as done.

## Contest reflection

- What went well?
- Where was time lost?
- Which pattern should be revisited?
- What will change in the next contest?
"""


def write_platform(platform: str, result: dict, now: int, code: dict[str, list[Path]]) -> list[str]:
    created = []
    for c in result["contests"]:
        if now < c["end"]:
            continue  # never publish anything about a contest that is still running
        contest_dir = ROOT / c["dir"]
        for p in c["problems"]:
            if p["slug"] in code and platform == "leetcode":
                created += write_code(contest_dir, p, code[p["slug"]])
        readme = contest_dir / "README.md"
        if readme.exists():
            readme.write_text(replace_block(readme.read_text(encoding="utf-8"), render_block(c, contest_dir)), encoding="utf-8")
        else:
            contest_dir.mkdir(parents=True, exist_ok=True)
            readme.write_text(new_contest_readme(c, contest_dir), encoding="utf-8")
            created.append(readme.relative_to(ROOT).as_posix())
    write_indexes(platform, result)
    return created


def write_indexes(platform: str, result: dict) -> None:
    groups: dict[Path, list[dict]] = {}
    for c in result["contests"]:
        if (ROOT / c["dir"] / "README.md").exists():
            groups.setdefault((ROOT / c["dir"]).parent / "README.md", []).append(c)
    if platform == "leetcode":
        for series in ("weekly", "biweekly"):
            groups.setdefault(ROOT / "contests" / "leetcode" / series / "README.md", [])
    else:
        groups.setdefault(ROOT / "contests" / platform / "README.md", [])
    for index, contests in groups.items():
        rows = ["| Date | Contest | Rank | Solved | Rating | Editorials |", "|---|---|---|---|---|---:|"]
        for c in sorted(contests, key=lambda c: -c["start"]):
            folder = ROOT / c["dir"]
            done = len(list(folder.glob("*/metadata.yaml")))
            rows.append(f"| {day(c['start'])} | [{c['title']}](./{folder.name}/) | {num(c['rank'])} | "
                        f"{c['solved'] if c['solved'] is not None else '—'} / {c['total'] if c['total'] is not None else '—'} | "
                        f"{c['rating']} ({signed(c['change'])}) | {done} |")
        if not contests:
            rows.append("| — | No synced contests yet | | | | |")
        summary = result.get("summary") if index.parent.name in (platform, "weekly") else None
        block = "\n".join([START, "", *( [summary, ""] if summary else []), *rows, "", END])
        text = index.read_text(encoding="utf-8") if index.exists() else f"# {PLATFORM_NAMES[platform]}\n"
        index.parent.mkdir(parents=True, exist_ok=True)
        index.write_text(replace_block(text, block), encoding="utf-8")


def run(fixtures: Path | None = None, only: str | None = None, env=os.environ, now: int | None = None,
        root: Path | None = None) -> bool:
    global ROOT
    ROOT = root or ROOT
    now = int(time.time()) if now is None else now
    state_file = ROOT / "data" / "contest-history.json"
    state = json.loads(state_file.read_text(encoding="utf-8")) if state_file.exists() else {}
    leethub = env.get("LEETHUB_DIR")
    code = leethub_code(Path(leethub) if leethub else None)
    ok = True
    for platform, (fetch, build) in PLATFORMS.items():
        if only and only != platform:
            continue
        prev = state.get(platform, {})
        try:
            if fixtures:
                f = fixtures / f"{platform}.json"
                if not f.exists():
                    continue
                snap = json.loads(f.read_text(encoding="utf-8"))
            else:
                handle = env.get(f"{platform.upper()}_HANDLE")
                if not handle:
                    print(f"{platform}: no {platform.upper()}_HANDLE set, skipped")
                    continue
                snap = fetch(handle, prev)
            result = build(prev, snap)
            created = write_platform(platform, result, now, code)
            state[platform] = result["state"]
            print(f"{platform}: {len(result['contests'])} contests; new files: {', '.join(created) or 'none'}")
        except Exception as e:  # one platform failing must not block the others
            ok = False
            print(f"{platform}: FAILED, nothing written. {e}", file=sys.stderr)
    state_file.parent.mkdir(parents=True, exist_ok=True)
    state_file.write_text(json.dumps(state, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return ok


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--fixtures", type=Path)
    parser.add_argument("--only", choices=tuple(PLATFORMS))
    args = parser.parse_args()
    return 0 if run(args.fixtures, args.only) else 1


if __name__ == "__main__":
    raise SystemExit(main())
