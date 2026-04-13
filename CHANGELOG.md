# Changelog

All notable changes to this project will be documented in this file.

Format based on [Keep a Changelog](https://keepachangelog.com/), versioning follows [Semantic Versioning](https://semver.org/lang/zh-TW/).

## [Unreleased]

## [0.5.0] - 2026-04-14

### Added

- feat: condition-rules-v2 — absolute additional whitelist, custom mode merge, differentiated summary per cube type
- feat: condition-rules-v3 — gear equipment type consolidation (6 → 4 types), `is_glove` / `is_hat` mutually-exclusive flags replacing `is_eternal`, FR-3 defense-in-depth gating so subtype flags only apply to gear
- feat: condition-rules-v3 Phase 2 — precise verbatim summary strings for preset and absolute-additional cubes (`支援 力 / 敏 / 智 / 幸、全屬、HP，包含 3S、雙 S 及全屬混搭`, `僅支援 99 四屬、77全、12 12 HP`, `支援 -1 -1 冷卻，也接受 77 全 冷卻；若洗到主屬會直接洗掉`, etc.)
- feat: 1920 × 1080 resolution hint label on main window for OCR accuracy guidance
- feat: sub-weapon physical / magic convertible preset option with widened 260px attribute combo
- feat: generalized crit damage OCR regex for observed M3 variants
- test: GUI tests for ConditionEditor helpers with Qt offscreen fixture
- test: ast-based locale sweep guarding against simplified-Chinese keywords in user-visible strings (FR-29)

### Fixed

- fix: Boss damage regex character order
- fix: expanded OCR corrections and skip tolerance for crit damage in custom mode

### Changed

- UI: 檢查更新 button restyled with Material Blue QSS (hover / pressed / disabled pseudo-states) so it is visually distinguishable as a button
- UI: checkbox label renamed 帽子 → 冷卻帽 to clarify the "roll a cooldown hat" scope (internal `is_hat` flag unchanged)
- condition rules: summary text adopts community shorthand notation (99 力 / 77 全 / 12 12 HP / 33 爆 / -1 -1 冷卻)
- sub-weapon: target attribute dropdown simplified to a single "物理/魔法攻擊力 (可轉換)" option
- refactor: unify preset dispatch via `_run_preset_any_pos` helper
- refactor: extract `_sync_subtype_checks`, `_toggle_subtype_mutex`, `_clear_custom_rows`, `_build_line_conditions` helpers in ConditionEditor

### Removed

- UI: GPU acceleration checkbox (feature discontinued; `AppConfig.use_gpu` dataclass field preserved to avoid breaking potential OCR engine references)
- internal: legacy config migration paths (`_OLD_EQUIP_MIGRATION` table and related compat keys) — release model is full-package redownload (A3 decision)
- internal: v2 dispatch symbols `GLOVE_TYPES` / `HAT_TYPES` / `ETERNAL_EQUIP_TYPES` / `_resolve_equip_type`

## [0.4.0] - 2026-04-06

### Added

- feat: display current version in window title bar
- feat: manual "check for update" button in status bar (queries GitHub Releases API)
- chore: add ruff linter as dev dependency

### Fixed

- fix: 13 new OCR misread corrections (crit damage, LIK/DIK, damage variants, HP recovery)
- fix: broaden crit damage pattern to catch unknown OCR misreads
- fix: debug screenshots not saving on Windows Unicode paths (cv2.imencode workaround)
- style: fix ruff E741 ambiguous variable names across codebase

## [0.3.0] - 2026-04-05

### Added

- feat: delay range hint and animation warning in settings panel
- feat: save debug screenshots (raw + processed) on every roll, keep last 10
- feat: release-notes skill for generating user-facing release notes
- CI: dev branch auto-build workflow (artifact only, no Release)
- CI: remove auto-generated release notes for manual editing
- docs: CHANGELOG
- docs: OCR bugfix log (`docs/ocr-bugfix-log.md`)
- docs: OCR matching feasibility study (`docs/features/ocr-matching/0-feasibility-study.md`)

### Fixed

- fix: worker not stopping after target condition reached (missing stop() call)
- fix: compound damage attributes misidentified when whitespace between characters
- fix: strip all Unicode whitespace in OCR preprocessing (not just ASCII spaces)
- OCR: attribute misreads (全屋性/全國性/全慶性 → 全屬性)
- OCR: INT character confusion (1NT/1IT/1TT/IIT/IT → INT, with boundary guard)
- OCR: trailing digits after % (+6%6 → +6%)
- OCR: percent misread as 9 (+79 → +7%, fallback only when normal parse fails)
- OCR: MaxHP/MaxMP prefix misread (axHP → MaxHP)
- OCR: debug image save log level (debug → warning)

### Changed

- delay defaults: 1500ms default, 1200-3000ms range (was 1000ms, 500-2000ms)
- delay resets to default on every app launch
- delay input auto-corrects to nearest valid value

## [0.2.0] - 2026-03-24

### Added

- CI: manual workflow dispatch for test builds
- CI: upload build directory for artifact downloads

### Fixed

- OCR: add corrections for 傷 misreads (佩害/集害/最終喜)
- OCR: disable doc_preprocessor to avoid UVDoc PermissionError

### Changed

- chore: enable console window for debugging

## [0.1.0] - 2026-03-15

### Added

- Core: screen capture, OCR (PaddleOCR chinese_cht), mouse control, template matching
- Core: condition checking with attribute pattern matching
- Core: cube rolling strategies (simple flow, compare flow)
- GUI: PyQt6 main window, region selector, settings panel, roll log
- Config: JSON save/load with serialization
- Tests: unit tests for condition parsing and config persistence
- Docs: architecture, GUI layout, implementation plan
