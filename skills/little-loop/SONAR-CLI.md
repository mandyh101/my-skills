# The Sonar CLI, and what it's actually good for

SonarSource ships a CLI (`sonar`, Homebrew `sonarqube-cli`) that talks to the same SonarCloud/SonarQube project CI gates against. Where it's installed and authenticated it removes a manual step from `little-address` and the end-of-loop gate, and adds a cheap secrets sweep before a push. It does **not** replace the gate.

## Is it here?

```bash
command -v sonar >/dev/null && sonar auth status
```

A connected CLI prints `[✓ Connected]`, the server and the org. Anything else — not on `PATH`, no token, wrong org — means **it isn't available**, and every step below falls back to the manual path. Never install it or run `sonar auth login` on the user's behalf: the token is theirs, and login is a browser flow no unattended run can finish.

## Which project?

Find the project key in this order, and stop at the first hit:

1. `sonar.projectKey` in `sonar-project.properties` at the repo root.
2. A `sonar` / `projectKey` line in the repo's `CLAUDE.md` or `AGENTS.md`.
3. Ask the user once, and suggest they add it to the repo's `CLAUDE.md`.

No key and no Sonar check on the repo's PRs means the repo doesn't use Sonar — skip every Sonar step and say so in the report.

## What a local scan does and doesn't catch

`sonar analyze` is a **secrets and security** scanner, not a local copy of the quality gate. It flags a hardcoded credential in under a second and flags **none** of the maintainability rules gates usually trip on (cognitive complexity, too many returns, nested ternaries).

So **a green `sonar analyze` is not a green quality gate** — never report it as one. Run it as a leak check over the change set:

```bash
sonar analyze --base <base branch>
```

A hit exits non-zero and is **blocking**. The fix is a rotated secret, not a later commit that redacts it — by then it's in branch history.

## What replaces the dashboard

Once a PR exists, the gate result and the issues behind it are fetchable.

**The gate — this is the authority:**

```bash
sonar api GET "/api/qualitygates/project_status?projectKey=<key>&pullRequest=<pr>"
```

Read `projectStatus.status` and each condition's `actualValue`.

**The issues — rule, message, `file:line`, everything a fix needs:**

```bash
sonar list issues --project <key> --pull-request <pr> --format table
```

`list issues` is **not filtered to open issues** — fixed ones keep appearing.

- Never conclude "still failing" from a non-empty issue list; check the gate.
- A row showing `file:?` (no line) has no anchor in current code — it's already fixed. A real `file:line` is live.
- An empty list on a failing gate means the analysis hasn't landed yet — wait for the check, not the clock.

## When it isn't there

Everything still works, it just costs a person. The gate's bot comment names the failing condition; its dashboard has the issue list. Where that needs a login, **ask the user to paste the issue list rather than guessing which rule fired from the diff**, and say in the report that the CLI wasn't available.
