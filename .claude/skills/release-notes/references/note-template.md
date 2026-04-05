# Release Notes Template

Use this template as a guide. Adapt sections based on actual changes — omit empty sections.

```markdown
## Bug Fixes
- <user-facing description of what was broken and how it's fixed>

## New Features
- <what users can now do that they couldn't before>

## Improvements
- <things that got better — performance, UX, accuracy>

## Known Issues
- <issues users should be aware of>

Full changelog: [`<prev-tag>...<tag>`](https://github.com/<owner>/<repo>/compare/<prev-tag>...<tag>)
```

## Writing Guidelines

| Principle | Example |
|-----------|---------|
| User language | "修正多個屬性辨識錯誤" not "fix regex pattern in condition.py" |
| Impact-focused | "潛能不再被誤判為未辨識" not "add _TRAILING_AFTER_PERCENT regex" |
| Concise | One line per item, no implementation details |
| Traditional Chinese | 台灣慣用詞彙（資料庫、程式、辨識） |

## What to Omit

These are internal changes that users don't care about:

- CI/CD workflow changes
- Test additions/modifications
- Code refactoring without user-visible impact
- Documentation updates
- Dependency bumps (unless security-related)
