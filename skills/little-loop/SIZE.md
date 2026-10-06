# PR size limit

little-loop is for **small PRs**. A PR a reviewer can read in one sitting gets a real review; one that can't gets skimmed. Work bigger than the limit wants splitting, or a bigger workflow (e.g. `slice-loop` where the repo has it).

## The limit

**300 changed lines or 10 files**, whichever trips first. Tests count. The plan doc, fixtures and lockfiles don't.

A repo can override it with a line in its `CLAUDE.md` or `AGENTS.md`:

```
little-loop size: 400 lines / 15 files
```

## Measuring it

```bash
git diff --shortstat <base>...HEAD -- . \
  ':(exclude)docs/plans/**' \
  ':(exclude,glob)**/fixtures/**' ':(exclude,glob)**/*.fixtures.*' \
  ':(exclude,glob)**/*.lock' ':(exclude,glob)**/*-lock.json' ':(exclude,glob)**/*-lock.yaml'
```

Changed lines = insertions + deletions. Use the plan doc's path in place of `docs/plans/**` if the repo keeps plans elsewhere. For a single phase, swap `<base>...HEAD` for that phase's commit range.

## The opt-out

Going over is allowed only on purpose. An **Opt-out:** line under the plan's **Total size** names why this PR can't be cut smaller, and the PR body repeats it so the reviewer knows before they start reading. Over the limit and silent about it is never allowed.

## Where it's checked

| When | Who | Over the limit means |
|---|---|---|
| Planning | little-plan | Estimate per phase + total. Flag it, don't trim silently |
| Sign-off | little-loop | Lead with it; user picks split / bigger workflow / opt-out |
| While building | little-implement | Phase well over its estimate → stop and report, don't commit |
| Verifying | little-verify | Phase size vs estimate — a finding, never a blocker |
| After each phase | little-loop | Running total over (or next phase would be) with no opt-out → pause |
| Report | little-loop | Actual vs limit; estimate vs actual goes in the run log |
