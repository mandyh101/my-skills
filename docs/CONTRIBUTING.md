# Contributing to my-skills

This is a personal skills repo — the workflow below is for future-you (or anyone else pushing changes), not a team process.

## Adding a new skill

1. Create the skill directory:
   ```bash
   mkdir -p skills/your-skill-name/references
   ```

2. Create `skills/your-skill-name/SKILL.md` with required frontmatter:
   ```markdown
   ---
   name: your-skill-name
   description: Brief description of what this skill does
   ---

   # Your Skill Title

   [Skill content and instructions]
   ```

   Add `disable-model-invocation: true` for a skill that should only run when dispatched by another skill or invoked by name — not picked automatically by description match.

3. Add reference files alongside `SKILL.md` as needed (see the little-loop family for the pattern: `SIZE.md`, `SONAR-CLI.md`, `RUN-LOG.md`, `PLAN-TEMPLATE.md`).

## Testing locally

```bash
claude --plugin-dir /path/to/my-skills
```

Or `/reload-plugins` from within Claude Code, then run the affected skill and check the output.

## Versioning

Bump the version in both `.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json` together — semantic versioning (major.minor.patch).

## Committing & pushing

```bash
git add skills/ docs/
git commit -m "Add/update skill-name: what changed and why"
git push origin main
```
