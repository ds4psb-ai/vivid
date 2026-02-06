# Academy Hardening Handoff

## Base
- Branch: `main`
- Baseline commit: `cd0c9eb0` (`feat(academy): simplify UX and stabilize nav/theme`)
- Goal: remove verbose/AI-like copy, reduce cognitive load, keep action-first UI

## Current Direction
- Minimize explanatory text
- Keep one primary action per section
- Prefer icon/button + short label over paragraphs
- Keep light/dark consistent via design tokens

## Priority Backlog
1. `P0` text pruning and IA tightening
- Make page subtitles optional
- Shorten academy nav labels to single-word/short labels
- Strip long explanatory paragraphs in `home/setup/credit/prompt/tools/vibe`
- Keep only action buttons and minimal status labels

2. `P1` visual consistency pass
- Remove remaining hardcoded `white/black/purple` utility usages in academy flow
- Normalize to `--fg-*`, `--surface-*`, `--border-*`

3. `P2` interaction hardening
- Ensure plus/add action remains prominent and clear
- Keep tooltip-based progressive disclosure for unfamiliar terms (e.g. anchor)

4. `P3` structure hardening
- Split large files (`AdminContent`, `DetectionResults`) into view/state units
- Remove dead exports/components

5. `P4` guardrails
- Add lint checks for forbidden UI classes in academy scope
- Add regression tests for nav and theme token invariants

6. `P5` final QA
- Mobile/desktop smoke on academy core tabs
- Light/dark visual sanity pass

## Quick Commands
- Target lint:
`cd frontend && npx eslint src/app/academy/components src/app/page.tsx src/config/sidebar-nav.ts`
- Tests:
`cd frontend && npm run test -- src/components/academy/nav-utils.test.ts src/app/globals.theme.test.ts`

