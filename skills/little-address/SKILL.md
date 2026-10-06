---
name: little-address
description: Work through review comments, failed checks and Sonar on a PR that little-loop raised, using its plan doc as context.
disable-model-invocation: true
---

# Little address

Deal with what came back on a little-loop PR. You run **after** the loop, on a branch someone is already reading — which shapes every rule here.

Start cold: the PR, its diff, and the plan doc. **Invoking this authorises commits and a push to that PR's branch** — never a force-push, amend or rebase.

## Step 0 — Confirm the loop raised this PR

```bash
gh pr view <pr> --json number,headRefName,baseRefName,state,url
gh repo view --json nameWithOwner -q .nameWithOwner
```

Check out the PR's branch, then look for its plan doc (`docs/plans/<TICKET>-*.md` or the repo's configured path) and run log (`~/.claude/loop-runs/<repo>/<TICKET>.md`).

- **Both found** → carry on.
- **Neither** → this isn't a little-loop PR. Say so in one line and handle the feedback as ordinary work.
- **One but not the other** → say what you found and ask.

Read the plan doc in full: acceptance criteria, Decided / Assumed, Non-goals and phases are what you triage against. Note whether Sonar is available ([`SONAR-CLI.md`](../little-loop/SONAR-CLI.md)).

**Completion criterion:** the PR traces to a plan doc and you've read it, or you've stopped and said why.

## Step 1 — Collect all of it

Feedback hides in five places. A pass that checks four looks complete while missing the substantive item — **review bodies** and **issue comments** are the usual misses.

```bash
gh pr checks <pr>                                                            # CI + Sonar gate
gh api repos/<owner/repo>/pulls/<pr>/comments --paginate --jq '.[] | {id, path, line, user: .user.login, body, in_reply_to_id}'
gh api repos/<owner/repo>/issues/<pr>/comments --paginate --jq '.[] | {id, user: .user.login, body}'
gh api repos/<owner/repo>/pulls/<pr>/reviews  --paginate --jq '.[] | {id, user: .user.login, state, body}'
```

Skip threads already resolved, and replies you posted in an earlier round. To see which threads are resolved:

```bash
gh api graphql -f query='query($o:String!,$r:String!,$n:Int!){repository(owner:$o,name:$r){pullRequest(number:$n){reviewThreads(first:100){nodes{isResolved comments(first:1){nodes{databaseId}}}}}}}' -F o=<owner> -F r=<repo> -F n=<pr>
```

**Sonar**: the bot comment names the failing condition, not the issues. With the CLI, get the gate and the issues directly ([`SONAR-CLI.md § What replaces the dashboard`](../little-loop/SONAR-CLI.md#what-replaces-the-dashboard)). Without it, **ask for the issue list to be pasted** rather than guessing which rule fired.

**Completion criterion:** every open comment, check and gate condition is in one list, each tagged with where it came from.

## Step 2 — Triage before touching code

Sort every item into exactly one bucket, and write the sort down:

- **Wrong assumption** — the plan guessed and the reviewer corrected it. The most valuable class: a planning failure that reached a PR. Fix it, and name it in the run log so retro can see what the planner keeps getting wrong.
- **Scope** — something shipped the plan didn't own, or a Non-goal the reviewer wants after all. Out of scope for this PR → reply with where it should go instead (a follow-up ticket).
- **Smell / CI** — mechanical: Sonar, a red job, a convention breach.
- **Disagree** — the comment misreads the code or the plan. **A reply, not a fix.**

None of them is "ask": where the fix is cheap and reversible, make it and say so — a reviewer objects to a commit more easily than they answer a question. The exception is a comment asking someone else for input; that's theirs to answer.

**Completion criterion:** every item sits in one bucket with its planned action written down before any edit.

## Step 3 — Fix exactly what was raised

New commits, one per coherent fix: `fix: <TICKET> <what the comment asked for>`. Nothing else rides along — a tidy-up sends the reviewer back to the top of a diff they'd already read.

If a fix reveals the PR was built on something false, **stop and tell the user** rather than reshaping the PR inside a review round.

**Completion criterion:** every item marked for fixing has a commit, and the diff holds nothing else.

## Step 4 — Re-run the gates, push once

Re-run the **Verify** commands of every phase your fixes touched, plus the repo's pre-PR checks and the Sonar secrets sweep where available. Quote the output.

Then push **once**, carrying every fix commit — a second push restarts CI before the first run finishes. Watch the checks (`gh pr checks <pr> --watch`, bounded at about ten minutes): a Sonar fix that doesn't move the gate isn't done.

Measure the PR's size per [`SIZE.md`](../little-loop/SIZE.md); if your fixes took it over the limit, say so in your replies' summary and the report.

**Completion criterion:** the gates pass, one push carries every fix, and the failed check or gate now passes (or is reported as still running).

## Step 5 — Reply to everything

Every item gets a reply, including the ones you didn't action. Reply to an inline comment's thread:

```bash
gh api repos/<owner/repo>/pulls/<pr>/comments/<comment-id>/replies -f body='(from Claude) <reply>'
```

Review bodies and issue comments get one PR comment answering each by quote (`gh pr comment <pr> --body …`).

- **Fixed** → what changed, and the commit sha. Nothing more.
- **Disagree** → why, in one sentence, without hedging. The reviewer decides.
- **Out of scope** → where it went instead.

Prefix every reply you post with `(from Claude)` so the thread reads as two voices. Never add it to someone else's words.

**Completion criterion:** no open comment is left without a reply.

## Step 6 — Log and report

Append to the run log per [`RUN-LOG.md`](../little-loop/RUN-LOG.md): `address: round <n> — <x> wrong-assumption, <y> scope, <z> smell/CI, <w> disagree`, naming each wrong assumption in a few words.

Report to the user: what you fixed (with shas), what you argued against, what went out of scope, check/gate status, and anything you stopped on. Once the PR is approved, the next step is `little-retro` before merging.

## Guardrails

- **New commits only.** Never amend, rebase or force-push a branch with an open PR — the reviewer must be able to see what changed since they read it.
- **A finding you think is wrong gets an argument, not a silent fix.**
- **Stay on this PR's branch.**
