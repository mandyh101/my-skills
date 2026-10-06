# Installation & Local Updates

## Install with marketplace plugin

```bash
# Add the marketplace
/plugin marketplace add mandyh101/my-skills

# Install the plugin
/plugin install my-skills@my-skills
```

## Local development & testing

Clone the repo:

```bash
git clone git@github.com:mandyh101/my-skills.git
cd my-skills
```

Point Claude Code to the local plugin directory:

```bash
claude --plugin-dir /path/to/my-skills
```

Or reload within Claude Code:

```
/reload-plugins
```

## Getting updates

```
/plugin marketplace update my-skills
/plugin update my-skills
```

Or, from a local clone:

```bash
cd /path/to/my-skills
git pull origin main
```

## Troubleshooting

**Plugin won't load locally**

```bash
claude plugin validate /path/to/my-skills
```

Check `.claude-plugin/plugin.json` exists and every skill has valid SKILL.md frontmatter.

**Skills not appearing after update**

```
/reload-plugins
```

Or clear the plugin cache and reinstall:

```bash
rm -rf ~/.claude/plugins/cache/my-skills/my-skills
/plugin install my-skills@my-skills
```
