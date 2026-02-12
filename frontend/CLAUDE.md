# Frontend CLAUDE.md

> **Prompty.co.kr** - Dual AI Tikitaka Workflow Guide Platform
> Next.js 16 + React 19 + TypeScript

---

## Quick Commands

```bash
npm run dev      # localhost:3100
npm run build    # Production build
npm run lint     # Lint
```

---

## Core Philosophy

```
Gemini CLI (video @mention) <-> Claude Antigravity
         |                         |
         +------ projects/{name}/ ------+
                      |
               STATE.md (shared state)
```

- **NOT**: AI calls/generates on your behalf
- **YES**: "Guide" for Dual AI Tikitaka + Critique record tracking

---

## Prompty Directory Structure

```
src/
├── app/                            # Prompty routes (root level)
│   ├── page.tsx                    # Landing/dashboard
│   ├── templates/                  # Template list/detail
│   ├── projects/                   # Project guide
│   │   └── [id]/
│   │       ├── page.tsx            # Workflow guide
│   │       └── critique/page.tsx   # Critique input
│   └── community/                  # Community
├── components/prompty/             # Prompty UI components
│   ├── CopyPromptButton.tsx        # Prompt copy
│   ├── GuideWorkflow.tsx           # 4-Stage progress bar
│   ├── CritiqueChecklist.tsx       # Evaluation checklist
│   └── ExternalToolLinks.tsx       # External tool links
└── lib/api.ts                      # API client
```

---

## 4-Stage Workflow

| Stage | Tool | Output |
|-------|------|--------|
| ANALYZE | Gemini CLI | ANALYSIS.md, PROFILES.md |
| IMAGE | NanoBanana, MJ | ANCHOR + scene images |
| VIDEO | Kling, Veo | Image-to-Video |
| ASSEMBLY | CapCut | Final edit |

---

## Critique Scoring Criteria

```
PASS   (85+)   -> Proceed to next stage
REVISE (60-84) -> Revise and regenerate (tikitaka)
REJECT (<60)   -> Review prompts
```

---

## Component Usage Examples

```tsx
import { 
  CopyPromptButton, 
  GuideWorkflow, 
  CritiqueChecklist 
} from '@/components/prompty';

// Prompt copy
<CopyPromptButton 
  promptText={step.prompt_text} 
  onCopy={handleCopyAnalytics} 
/>

// 4-Stage progress bar
<GuideWorkflow 
  stages={guide.stages}
  currentStage="stage2"
  progressPercent={60}
/>

// Critique checklist
<CritiqueChecklist
  items={template.critique_config.items}
  scores={scores}
  onScoreChange={handleScore}
  passingScore={85}
/>
```

---

## API Client

```typescript
import { api } from '@/lib/api';

// Template list
const templates = await api.getPromptyTemplates();

// Project Guide
const guide = await api.getPromptyGuide(projectId);

// Submit Critique
await api.submitPromptyCritique(projectId, stage, stepId, scores);

// Action log
await api.logPromptyAction(projectId, 'copy_prompt', stage, step);
```

---

## Environment Variables

```bash
NEXT_PUBLIC_API_URL=http://127.0.0.1:8100
```

---

## SSoT References

```
viral-video-automation/templates/
├── CRITIQUE_IMAGE.md    # Image evaluation criteria
├── CRITIQUE_VIDEO.md    # Video evaluation criteria
├── CRITIQUE_SELFLOOP.md # Self-Loop flow
└── MODE_TIKITAKA.md     # Tikitaka UX
```
