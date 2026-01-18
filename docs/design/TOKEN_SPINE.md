# Token Spine (Step 1)

**Date**: 2026-01-18  
**Purpose**: Define the base token spine so downstream component tokenization stays stable.

> This step **adds tokens only** (no UI change). All keys are present in both light/dark theme scopes where applicable.

---

## 1) Role Tokens (Primary / Secondary / Tertiary)

| Token | Light | Dark | Notes |
|---|---|---|---|
| `--role-primary-bg` | `--interactive-default` | `--interactive-default` | Primary action background |
| `--role-primary-fg` | `--fg-on-emphasis` | `--fg-on-emphasis` | Primary text/icon |
| `--role-primary-border` | `--interactive-default` | `--interactive-default` | Primary border |
| `--role-secondary-bg` | `--surface-1` | `--surface-1` | Secondary action surface |
| `--role-secondary-fg` | `--fg-0` | `--fg-0` | Secondary text |
| `--role-secondary-border` | `--border-muted` | `--border-muted` | Secondary border |
| `--role-tertiary-bg` | `transparent` | `transparent` | Ghost button bg |
| `--role-tertiary-fg` | `--fg-muted` | `--fg-muted` | Ghost text |
| `--role-tertiary-border` | `transparent` | `transparent` | Ghost border |

---

## 2) Spacing Tokens

| Token | Value |
|---|---|
| `--space-0` | 0px |
| `--space-1` | 4px |
| `--space-2` | 8px |
| `--space-3` | 12px |
| `--space-4` | 16px |
| `--space-5` | 20px |
| `--space-6` | 24px |
| `--space-7` | 32px |
| `--space-8` | 40px |
| `--space-9` | 48px |
| `--space-10` | 64px |

---

## 3) Radius Tokens

| Token | Value |
|---|---|
| `--radius-xs` | 6px |
| `--radius-sm` | 8px |
| `--radius-md` | 12px |
| `--radius-lg` | 16px |
| `--radius-xl` | `--radius-lusion` (20px) |
| `--radius-2xl` | 24px |
| `--radius-pill` | 999px |

---

## 4) Motion Tokens

| Token | Value |
|---|---|
| `--motion-duration-fast` | 120ms |
| `--motion-duration-medium` | 200ms |
| `--motion-duration-slow` | 320ms |
| `--motion-duration-xslow` | 500ms |
| `--motion-ease-standard` | `--ease-lusion` |
| `--motion-ease-emphasized` | `--ease-bounce` |
| `--motion-ease-linear` | linear |

---

## 5) Z-Index Tokens

| Token | Value |
|---|---|
| `--z-base` | 0 |
| `--z-sticky` | 40 |
| `--z-dropdown` | 50 |
| `--z-overlay` | 60 |
| `--z-modal` | 70 |
| `--z-toast` | 90 |

---

## 6) Shadow Tokens

| Token | Value | Notes |
|---|---|---|
| `--shadow-color-ambient` | rgba(2, 6, 23, 0.08) | base shadow color |
| `--shadow-color-lifted` | rgba(2, 6, 23, 0.18) | raised surfaces |
| `--shadow-sm` | 0 1px 2px var(--shadow-color-ambient) | subtle |
| `--shadow-md` | 0 6px 16px var(--shadow-color-ambient) | mid |
| `--shadow-lg` | 0 14px 40px var(--shadow-color-lifted) | strong |

---

## Notes

- Step 1 introduces **spine tokens only** (no component changes).
- High-contrast / forced-color variations are handled in preference modes.
- Next step: **Component tokenization** using these spine values.
