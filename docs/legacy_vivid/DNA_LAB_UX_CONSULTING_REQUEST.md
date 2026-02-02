# DNA Lab UX Consulting Request

> **Date**: 2026-01-30
> **Product**: Crebit Studio - DNA Lab
> **Request**: UX Architecture Review & Improvement Recommendations

---

## 1. Product Context

### What is DNA Lab?

DNA Lab is a creative analysis tool that extracts "directorial DNA" from video content. It analyzes cinematography, color grading, camera techniques, and narrative structure to create reusable style profiles.

### Core Value Proposition

```
"Analyze master filmmakers' styles and apply them to your own creative work"
```

### Target Users

- Independent filmmakers
- Content creators
- Video production studios
- Film students

---

## 2. Current Architecture

### Tech Stack
- **Frontend**: Next.js 16, React 19, TypeScript, Tailwind CSS
- **Backend**: FastAPI, Python, PostgreSQL
- **Deployment**: Vercel (frontend), Railway (backend)

### Current URL Routing

```
/dna-lab                    → Onboarding OR Overview (conditional)
/dna-lab?ip={slug}          → Overview with IP context
/dna-lab?step={stepId}      → Step detail view
/dna-lab?step=vpe           → Video Analysis step
/dna-lab?step=ad            → Aesthetic Director step
/dna-lab?step=mirror        → Creative DNA step
/dna-lab?step=qc            → Quality Control step
```

### Current Component Hierarchy

```
DNALabPage (page.tsx)
├── Condition: No session → DNALabOnboarding
│   ├── Option 1: Select existing IP
│   ├── Option 2: Enter video URL
│   └── Option 3: Quick start with master style
│
├── Condition: Has IP/Session → DNALabOverview
│   └── 2x2 Grid of 4 steps
│       ├── 영상 분석 (Video Analysis)
│       ├── 미학 적용 (Aesthetic Application)
│       ├── 창작 DNA (Creative DNA)
│       └── 품질 검증 (Quality Control)
│
└── Condition: step param → StepContent
    └── Individual panel (VPEPanel, AestheticDirectorPanel, etc.)
```

---

## 3. Current UI State (After Recent Simplification)

### Overview Screen (2x2 Grid)

```
┌─────────────────────────────────────────────────┐
│                                                 │
│  DNA 분석                                       │
│  단계를 선택해서 시작하세요.                    │
│                                                 │
├─────────────────────────────────────────────────┤
│                                                 │
│  ┌─────────────────┐  ┌─────────────────┐      │
│  │ 🎬              │  │ 🎨              │      │
│  │ 영상 분석       │  │ 미학 적용       │      │
│  │ Logic Vector... │  │ 거장 스타일...  │      │
│  └─────────────────┘  └─────────────────┘      │
│                                                 │
│  ┌─────────────────┐  ┌─────────────────┐      │
│  │ 🧠              │  │ ✅              │      │
│  │ 창작 DNA        │  │ 품질 검증       │      │
│  │ 페르소나 분석   │  │ 최종 검수       │      │
│  └─────────────────┘  └─────────────────┘      │
│                                                 │
└─────────────────────────────────────────────────┘
```

### Step Detail Screen (Example: VPE)

```
┌─────────────────────────────────────────────────┐
│ [Workflow Progress Bar: VPE → AD → Mirror → QC] │
├─────────────────────────────────────────────────┤
│                                                 │
│  VPEPanel Component                             │
│  ├── Video URL input                            │
│  ├── Analysis options                           │
│  ├── Run button                                 │
│  └── Results display                            │
│                                                 │
└─────────────────────────────────────────────────┘
```

---

## 4. Business Logic & Data Flow

### Pre-analyzed Master Directors (Auteurs)

We have **pre-analyzed DNA profiles** for master filmmakers:

| Auteur Key | Name | Style Characteristics |
|------------|------|----------------------|
| `bong` | 봉준호 (Bong Joon-ho) | Conflict-driven, cold tones, frame-within-frame |
| `nolan` | Christopher Nolan | Non-linear time, grand scale, IMAX |
| `wong` | Wong Kar-wai | Saturated colors, slow motion, urban melancholy |
| `kubrick` | Stanley Kubrick | Symmetry, one-point perspective, long takes |
| `fincher` | David Fincher | Dark palette, precise camera movement |

### User Journey Scenarios

**Scenario A: Apply Existing Master Style**
```
1. User lands on /dna-lab
2. Sees onboarding options
3. Clicks "Quick Start" → selects master (e.g., Bong)
4. Views pre-analyzed DNA profile
5. Clicks "Apply to Story Engine"
6. Creates content using that style
```

**Scenario B: Analyze New Video**
```
1. User lands on /dna-lab
2. Selects "Enter URL" or uploads video
3. System analyzes video (VPE → AD → Mirror → QC)
4. User views generated DNA profile
5. Saves to their IP collection
6. Uses in future projects
```

**Scenario C: Browse Existing IP**
```
1. User has existing IP (project) with saved DNA
2. Navigates to /dna-lab?ip=my-project
3. Views/edits existing DNA profile
4. Continues workflow from any step
```

### Chain Data Flow

```
VPE (Video) ──────────────────────────────────────────────────┐
│ Output: Logic Vector (emotional arc, structure)             │
└──────────────────────────────────────────────────────────────┤
                                                               │
AD (Aesthetic) ←───────────────────────────────────────────────┤
│ Input: Logic Vector                                          │
│ Output: Color palette, visual guidelines                     │
└──────────────────────────────────────────────────────────────┤
                                                               │
Mirror (Creative DNA) ←────────────────────────────────────────┤
│ Input: Logic Vector + Aesthetic Guidelines                   │
│ Output: Persona DNA, technique analysis                      │
└──────────────────────────────────────────────────────────────┤
                                                               │
QC (Quality) ←─────────────────────────────────────────────────┘
│ Input: All previous outputs
│ Output: Quality report, recommendations
```

---

## 5. Known UX Problems

### Problem 1: Unclear Entry Point
- Users don't know what to do first
- 4 steps shown simultaneously without context
- No clear hierarchy of importance

### Problem 2: Mixed Mental Models
- Pre-analyzed masters vs new video analysis are different flows
- Current UI treats them the same way
- Confusing for first-time users

### Problem 3: Information Overload (in step details)
- Too many options visible at once
- Technical terminology (Logic Vector, VPE, etc.)
- Missing progressive disclosure

### Problem 4: Unclear Progress
- No clear indication of current position in workflow
- Steps can be accessed non-sequentially
- Missing data requirements not obvious

---

## 6. Design Constraints

### Must Keep
1. **UnifiedWorkflowShell** - Shared component across 3 mega apps
2. **4-step workflow** - VPE → AD → Mirror → QC (core business logic)
3. **IP-based data persistence** - Projects save to IP slugs
4. **Chain data dependencies** - Steps depend on previous outputs

### Can Change
1. Entry flow (onboarding)
2. Overview layout
3. Step detail layout
4. Navigation patterns
5. Visual design (within design system)

### Design System Variables
```css
--bg-base: #0a0a0a
--bg-subtle: #111111
--fg-primary: #ef4444 (red accent)
--border-primary: #ef4444
```

---

## 7. Questions for Designer

### Architecture Questions

1. **Entry Flow**: Should we separate "Browse Masters" and "Analyze New" into distinct entry points? Or keep unified?

2. **URL Routing**: Is query-param-based routing (`?step=vpe`) acceptable, or should we use path-based (`/dna-lab/vpe`)?

3. **Overview vs Direct Entry**: When user has context (IP), should they land on Overview or jump to relevant step?

### UX Pattern Questions

4. **Progressive Disclosure**: How much information should be visible on Overview vs hidden in detail views?

5. **Non-sequential Access**: Users can jump between steps. How do we handle missing data gracefully?

6. **Micro-interactions**: What feedback is needed during analysis (loading states, progress, completion)?

### Visual Design Questions

7. **Grid Layout**: Is 2x2 optimal for 4 steps, or consider other layouts (linear, hub-spoke)?

8. **Step Cards**: What information density is appropriate per card?

9. **Empty States**: How should we handle steps with no data yet?

---

## 8. Competitive Reference

### Similar Products (for reference)

| Product | Pattern |
|---------|---------|
| Figma | Hub-spoke, progressive disclosure |
| Notion | Linear wizard for complex tasks |
| Linear | Keyboard-first, minimal chrome |
| Runway ML | Step-by-step video generation |
| Descript | Timeline-based editing |

---

## 9. Success Metrics

What would "good UX" look like?

1. **Time to First Action**: < 10 seconds from landing to meaningful interaction
2. **Completion Rate**: > 70% of users complete at least one analysis
3. **Return Usage**: Users come back for multiple sessions
4. **Error Recovery**: Users can recover from mistakes without starting over

---

## 10. Appendix: Code References

### Key Files

| File | Purpose |
|------|---------|
| `frontend/src/app/dna-lab/page.tsx` | Main page routing logic |
| `frontend/src/components/workflow/DNALabOverview.tsx` | Overview 2x2 grid |
| `frontend/src/components/workflow/UnifiedWorkflowShell.tsx` | Shared shell component |
| `frontend/src/components/dna-lab/DNALabOnboarding.tsx` | Entry onboarding |

### Current DNALabOverview Implementation

```tsx
// Simplified 2x2 grid (current state)
const STEPS = [
  { id: "vpe", name: "영상 분석", subtitle: "Logic Vector 추출", icon: Video },
  { id: "ad", name: "미학 적용", subtitle: "거장 스타일 적용", icon: Palette },
  { id: "mirror", name: "창작 DNA", subtitle: "페르소나 분석", icon: Brain },
  { id: "qc", name: "품질 검증", subtitle: "최종 검수", icon: CheckCircle },
];

export function DNALabOverview({ ipSlug, onStepClick }) {
  return (
    <div className="p-6 max-w-4xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white mb-2">
          DNA <span className="text-[var(--fg-primary)]">분석</span>
        </h1>
        <p className="text-gray-400">단계를 선택해서 시작하세요.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {STEPS.map((step) => (
          <button onClick={() => onStepClick(step.id)} className="...">
            <Icon /> {step.name} {step.subtitle}
          </button>
        ))}
      </div>
    </div>
  );
}
```

---

## 11. Requested Deliverables

1. **UX Audit**: Review current state, identify critical issues
2. **Flow Recommendations**: Suggested user journey improvements
3. **Wireframes**: Low-fidelity mockups of recommended changes
4. **Priority Matrix**: What to fix first vs later

---

**Contact**: [Your contact info]
**Repository**: Private (can provide access if needed)
**Live URL**: https://prompty.co.kr/dna-lab

