---
name: release-notes
description: "Generate and publish release notes for a GitHub Release. Use when: user says 'release notes', 'generate release notes', 'write release notes', 'update release', or after tagging a version. Not for: creating tags (user does that manually), changelog updates (edit CHANGELOG.md directly)."
allowed-tools: Bash(git:*), Bash(gh:*), Read, Grep, AskUserQuestion
---

# Release Notes

Generate user-facing release notes in Traditional Chinese from git history and CHANGELOG, then apply to a GitHub Release via `gh release edit`.

## Workflow

```
Detect tag → Find previous tag → Collect changes → Read CHANGELOG → Draft notes → User confirm → Apply
```

### Step 1: Detect Target Tag

If the user provides a tag (e.g., `/release-notes v0.2.1`), use it directly.

Otherwise, auto-detect the latest tag:

```bash
git tag --list 'v*' --sort=-v:refname | head -1
```

Verify the tag has a corresponding GitHub Release:

```bash
gh release view <tag> --json tagName,name,body
```

If no Release exists yet, inform the user and stop — the workflow expects the CI to create the Release first.

### Step 2: Find Previous Tag

```bash
git tag --list 'v*' --sort=-v:refname | head -2 | tail -1
```

If only one tag exists (first release), use the initial commit as base.

### Step 3: Collect Changes

```bash
git log <prev-tag>..<tag> --oneline --no-merges
```

### Step 4: Read CHANGELOG (Optional)

Check if `CHANGELOG.md` exists and has a section for this version:

```bash
grep -A 50 "## \[$(echo <tag> | sed 's/^v//')\]" CHANGELOG.md
```

If found, use it as reference for organizing the notes. If not found, generate purely from git log.

### Step 5: Draft Release Notes

Write notes following the template in `references/note-template.md`. Key principles:

- Write in **Traditional Chinese** (台灣慣用詞彙)
- Use **user language**, not developer jargon
- Group by user impact (bug fixes, new features, improvements), not by file or commit type
- Omit internal changes users don't care about (CI, refactoring, test-only changes)
- Include a compare link at the bottom

### Step 6: User Confirmation

Present the draft to the user via AskUserQuestion. The user can approve or request changes.

### Step 7: Apply

```bash
gh release edit <tag> --notes "<approved notes>"
```

Verify:

```bash
gh release view <tag> --json body --jq '.body' | head -20
```

## Arguments

| Arg | Description |
|-----|-------------|
| `<tag>` | Target tag (default: latest tag) |
| `--dry-run` | Generate notes but don't apply (just output) |

## Examples

```bash
/release-notes
/release-notes v0.2.1
/release-notes --dry-run
```
