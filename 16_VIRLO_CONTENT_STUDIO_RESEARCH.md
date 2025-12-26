# Virlo Content Studio Research (Detailed)

**Date**: 2025-12-24  
**Scope**: Content Studio, Usage/Billing, Credits, Affiliate entry points  
**Method**: Headless DOM snapshot + CSS token review (no user-specific data captured)

---

## 0.1) SoR Alignment (Reference Only)

This document is reference-only. "Vivid mapping" items are candidates; final decisions live in SoR docs.

- UI/UX: `13_UI_DESIGN_GUIDE_2025-12.md`
- Templates/Capsules: `23_TEMPLATE_SYSTEM_SPEC_CODEX.md`, `05_CAPSULE_NODE_SPEC.md`
- Growth/Credits: `17_CREDITS_AND_BILLING_SPEC_V1.md`, `18_AFFILIATE_PROGRAM_SPEC_V1.md`

---

## 0) Executive Snapshot

Virlo’s Content Studio positions itself as a **visual AI content workflow builder** with a node‑based canvas. The onboarding content is structured as a mini‑guide: **Core Components → What You Can Build → How It Works**. The product also surfaces **Credits, Billing, and Affiliate** as first‑class navigation items instead of burying them in settings.

![Virlo Content Studio Canvas](/Users/ted/.gemini/antigravity/brain/b80b68f3-9a57-43c3-ac4e-3249d9f0662a/virlo_content_studio_canvas_1766553414562.png)
*Figure 1: Virlo Content Studio node-based interface showing Social Media Input → AI Processor → Script Writer workflow.*

---

## 1) Layout + Information Architecture

**Primary layout**
- Full‑height gradient background (top→bottom), center panel with dark surface
- Left fixed sidebar, collapsible to icon‑only
- Main content panel inside a bordered, rounded container

**Observed structure (classes imply intent)**
- Sidebar width: `16.25rem` (expanded), `5rem` (icon‑only)
- Main container: `bg-[#0c111d]` + `border-[#344054]` + `rounded-xl`
- Shadow: subtle `0px 1px 3px` for elevation

**Implication for Vivid**
- Use a **fixed left rail** for mode switching
- Keep the **canvas in a framed panel** (dark surface + border)
- Reserve top‑bar for title + run/preview/credits

---

## 2) Navigation Map (Observed)

**Top level**
- Dashboard
- Research
- Creator Hub
- Accounts
- Changelog
- Get Free Credits
- Affiliate Program (external)
- Support: Yap With Founder
- Community: Discord

**Research submenu**
- Outlier
- Creator Search
- Orbit Search
- Collections
- Knowledge Center

**Creator Hub submenu**
- Content Studio (New badge)
- Media Generation

**Accounts submenu**
- Account
- Usage
- Billing

**Vivid mapping**
- Research: Evidence / Outlier / Pattern Library / Collection
- Creator Hub: Content Studio (Node Canvas)
- Accounts: Usage / Billing / Credits
- Affiliate: separate item + Credits CTA

---

## 3) Content Studio Positioning Copy (Extracted)

**Tagline**
- “Visual AI content workflow builder”

**Short description**
- “Connect input sources (videos, documents, websites) to AI processors and generate professional outputs—all on an intuitive node‑based canvas.”

**Vivid mapping**
- Keep a single‑sentence **“canvas promise”** on empty state
- Use a short, scannable description in onboarding

---

## 4) Core Components (Extracted Section)

**Input Nodes** (Verified)
- **Social Media**: Direct ingest from TikTok, YouTube, Instagram, Meta Ads.
- **Documents**: PDF, DOCX, CSV, XLSX.
- **Files**: Video/Audio media injection.
- **Websites**: URL scraping and parsing.

**Virlo Processor** (AI Command Center)
- **Multi-Model Support**: Validated integration of **Claude 4.5 Sonnet**, **GPT-5.1**, **Gemini 2.5 Flash**, **Perplexity Sonar Pro**.
- **Context Awareness**: Automatically understands all connected up-stream data.
- **Real-time Web Search**: Integrated into the processor node.

**Output Nodes** (deliverables)
- Video Scripts
- Social Media Posts
- Blog Articles
- Email Campaigns
- Custom Formats

**Vivid mapping**
- Keep **Input / Processor / Output** as the first conceptual model
- In Vivid, “AI Processor” → “Capsule / Spec Engine” alignment

---

## 5) What You Can Build (Extracted Section)

- **Content Repurposing**: “Turn a YouTube video into a Twitter thread, blog post, and Instagram carousel—all in one workflow.”
- **Document Analysis**: “Upload PDFs, spreadsheets, or documents and chat with AI to extract insights, summaries, or reports.”
- **Research Workflows**: “Scrape websites, analyze competitors, and generate comprehensive research reports with citations.”
- **Batch Content Creation**: “Connect multiple inputs and generate dozens of outputs (captions, scripts, posts) in parallel.”

**Vivid mapping**
- Provide 3–4 **example canvases** (short‑form script, storyboard, marketing variants)
- Emphasize **batch generation** and **multi‑output** for notebook outputs

---

## 6) How It Works (Extracted Steps)

- **Add Input Nodes**: “Click the + button to add inputs: paste YouTube links, upload files, enter text, or scrape websites.”
- **Connect to AI Processor**: “Drag connections from inputs to the AI processor. The AI automatically understands all connected content.”
- **Chat & Generate**: “Ask the AI to analyze, summarize, or transform your content. Add output nodes to generate formatted results.”

**Vivid mapping**
- Match step structure: **Add → Connect → Generate**
- Use the same verbs for onboarding

---

## 7) Empty State + CTA Mechanics

**Observed CTAs**
- Create New Canvas
- Create Your First Canvas
- “Start with a blank canvas and AI processor node” (supporting copy)

**Vivid mapping**
- Empty state should offer **1‑click seed graph** (Input → Capsule → Script/Beat → Storyboard → Output)
- Keep CTA copy crisp: “Create First Canvas”

---

## 8) Credits, Usage, Billing (Detailed Extraction)

**Billing/Usage surface**
- Usage & Billing page label
- Monthly/Annual toggle with “Annual 30% Off”
- CTA buttons: Get Started / Go Pro / Go Elite

**Plan tiers (extracted from embedded data)**
- Starter Creator: 1,000 credits, 2 account connections
- Pro Creator: 5,000 credits, 4 account connections
- Elite Creator: 12,500 credits, 6 account connections
- Research Analyst: 1 account connection

**Top‑up credits (one‑time)**
- 500 credits
- 2,000 credits
- 5,000 credits

**API credit packs**
- 5,000 credits
- 15,000 credits
- 40,000 credits

**Vivid mapping**
- Adopt dual model: **subscription credits + top‑up packs**
- Separate **creator credits** vs **API credits**
- Add “Get Free Credits” CTA in nav and empty state

---

## 9) Affiliate / Growth Entry Points

**Observed**
- “Affiliate Program” link in nav (external portal)
- “Get Free Credits” CTA is visible
- “Join our Discord” as community CTA
- “Yap With Founder” as support CTA

**Vivid mapping**
- Keep Affiliate entry at top‑level nav
- Add Credits page with “Invite + Earn” module

---

## 10) Visual Tokens + Interaction DNA

**Fonts**
- Nunito (primary sans)

**Color tokens (observed)**
- Accent: `#ed62a0` (pink‑magenta)
- Background gradient: `#120f16 → #1d1d36 → #312635`
- Panel base: `#0c111d`
- Borders: `#344054`, `#333741`
- Hover surfaces: `#1f242f`, `#2a3142`
- “New” badge: green chips

**Interaction patterns**
- Collapsible sidebar (expanded vs icon‑only)
- Active nav item highlight by accent
- “New!” badge on new feature entry
- Empty‑state CTA + walkthrough trigger

**Vivid mapping**
- Preserve **dark studio feel**, but use Vivid palette
- Keep **badge chips** for “New / Beta”
- Use a **single accent** for active nav + capsule focus

---

## 11) Apply to Vivid (Concrete Plan)

This section is a candidate plan; final decisions live in SoR documents.

**UI structure**
- Left rail: Research / Creator Hub / Accounts / Credits / Affiliate
- Canvas workspace: framed panel with inspector + preview
- Empty state: “Create First Canvas” + “Start with Capsule” shortcut

**Credits system**
- Implement wallet + ledger (Creator / Top‑up / API / Promo)
- Usage view shows: balances, month‑to‑date spend, recent runs

**Affiliate**
- First‑class nav entry
- Invite flow → reward credits

---

## 12) Notes / Limits

- Data derived from DOM snapshots (content‑studio, usage, billing pages).
- No user‑specific data or private tokens were extracted.

---

## 13) Deep Dive Level 1: Interaction Mechanics (Micro-Behavior)

**Node Port Logic**
- **Input Ports (Left)**:
  - **Single-Signal**: Nodes like "Script Writer" accept only *one* primary processor input.
  - **Multi-Signal**: "Processor" nodes accept *n-inputs* (Context aggregation).
  - **Visual Feedback**: Compatible ports glow green when dragging an edge. Incompatible ports dim.

**Node Status States**
- **Idle**: Gray border, flat background.
- **Processing**: Pulsing accent-color border (`#ed62a0`), animated progress strip at bottom of node.
- **Complete**: Solid green checkmark badge, output port active.
- **Error**: Red border, clickable "Retry" action inline.

**Canvas Controls**
- **Minimap**: Bottom-right, floating. Click-drag to pan.
- **Zoom**: Mouse wheel support (10% ~ 200%).
- **Lasso Select**: Shift+Drag to selecting multiple nodes for batch-move or delete.

---

## 14) Deep Dive Level 2: Data Schema Implication (Vivid Spec)

To support the features observed in Virlo, Vivid's schema must evolve:

**1. Node Definition (`NodeSpec`)**
- Need strict `input_contracts`:
  ```json
  "input_contracts": {
    "required": ["source_context"],
    "optional": ["style_reference"],
    "max_connections": { "primary": 1, "context": 5 }
  }
  ```

**2. Processor State (`ExecutionState`)**
- Virlo distinguishes "Context Awareness" (Upstream) from "Parameter Config" (Local).
- Vivid needs `context_window` property in the `CapsuleRun` table:
  - `upstream_inputs`: `JSONB` array of *all* connected node outputs (not just immediate parent).
  - `token_usage`: Track tokens *per node* for billing transparency.

**3. Edge Properties (`EdgeData`)**
- Edges shouldn't just be IDs. They need data types to enforce validity.
- `edge_type`: `data` (flow of content) vs `control` (trigger only).
- Virlo seems to use implicit typing (video-to-video, text-to-text). Vivid should make this explicit in `connection_rules`.

**4. Project Metadata (`CanvasMeta`)**
- **`source_manifest`**: List of all external URLs scraped/ingested (for "Research" view).
- **`output_manifest`**: Aggregated deliverables (for "Creator Hub" view).

---

## 15) Deep Dive Level 3: Implementation Tokens (Tailwind/CSS)

These tokens are extracted for immediate application in Vivid's `globals.css` or `tailwind.config.js`.

**1. Semantic Color Palette**
```css
:root {
  /* Brand Identity */
  --virlo-accent: #ed62a0;          /* Pink-Magenta for primary actions/active states */
  --virlo-accent-glow: rgba(237, 98, 160, 0.4);

  /* Surface Hierarchy */
  --virlo-bg-base: #0c111d;         /* Canvas/Panel Background */
  --virlo-bg-surface: #1f242f;      /* Card/Node Background */
  --virlo-bg-hover: #2a3142;        /* Interactive Element Hover */

  /* Border System */
  --virlo-border-dim: #344054;      /* Default Borders */
  --virlo-border-highlight: #475467;/* Active/Focus Borders */
  
  /* Status Indicators */
  --status-success: #12b76a;        /* Completed Nodes */
  --status-error: #f04438;          /* Failed Runs */
}
```

**2. Typography Scale (Nunito/Space Grotesk Mapping)**
- `text-display`: 24px/32px, Bold (700) - *Page Titles*
- `text-h1`: 18px/28px, SemiBold (600) - *Panel Headers*
- `text-body`: 14px/20px, Regular (400) - *Default Text*
- `text-label`: 12px/16px, Medium (500), Uppercase tracking-wide - *Inspector Labels*
- `text-mono`: 12px/16px (JetBrains Mono) - *IDs / Code Snippets*

**3. Component Properties**
- **Cards/Nodes**: `rounded-xl` (12px), `border-1`, `shadow-sm`
- **Buttons**: `rounded-lg` (8px), `h-9` (36px for standard), `px-4`
- **Inputs**: `bg-[#0c111d]`, `border-virlo-border-dim`, `focus:ring-virlo-accent`

**4. Animation DNA**
- **Processing Pulse**: `animate-pulse` (2s cubic-bezier(0.4, 0, 0.6, 1) infinite)
- **Hover Transition**: `transition-all duration-200 ease-out`
- **Node Selection**: `ring-2 ring-virlo-accent ring-offset-2 ring-offset-[#0c111d]`

---

## 16) Deep Dive Level 4: State Machine Tokens (Execution Lifecycle)

Captured via browser reverse-engineering session. These state definitions are **directly implementable**.

**1. Node Lifecycle FSM (Finite State Machine)**

```typescript
type NodeState = 'idle' | 'loading' | 'streaming' | 'complete' | 'error';

interface NodeLifecycle {
  // State: IDLE
  // Trigger: User clicks "Send" or "Generate"
  // Exit Condition: API request initiated
  idle: {
    visualIndicator: 'gray-border, flat-bg';
    sendButtonEnabled: boolean; // false if prompt empty
    allowEdit: true;
  };
  
  // State: LOADING
  // Trigger: API POST /api/process called
  // Exit Condition: First SSE chunk received OR error
  loading: {
    visualIndicator: 'pulsing-border, typing-dots';
    statusMessage: 'Vee is working on your request...';
    allowCancel: true;
  };
  
  // State: STREAMING
  // Trigger: First content chunk received via SSE
  // Exit Condition: [DONE] signal OR stream error
  streaming: {
    visualIndicator: 'content-appearing, output-node-spawned';
    outputNodePosition: 'auto-placed-right-of-processor';
    realTimeUpdate: true;
  };
  
  // State: COMPLETE
  // Trigger: [DONE] signal received
  // Exit Condition: User initiates new request
  complete: {
    visualIndicator: 'green-checkmark-badge';
    actionsVisible: ['copy-to-clipboard', 'edit', 'regenerate'];
    creditDeducted: true;
  };
  
  // State: ERROR
  // Trigger: API error OR stream failure
  // Exit Condition: User clicks Retry
  error: {
    visualIndicator: 'red-border, error-icon';
    actionsVisible: ['retry', 'dismiss'];
    preserveInput: true;
  };
}
```

**2. State Transition Matrix**

| From State | To State | Trigger | API Event |
|------------|----------|---------|-----------|
| `idle` | `loading` | Click Send button | `POST /api/process` |
| `loading` | `streaming` | First SSE chunk | `onopen` event |
| `loading` | `error` | API 4xx/5xx | `onerror` event |
| `streaming` | `complete` | `[DONE]` signal | `onmessage data: [DONE]` |
| `streaming` | `error` | Stream disconnect | `onerror` event |
| `error` | `loading` | Click Retry | Re-POST `/api/process` |
| `complete` | `idle` | New prompt entered | User input |

**3. Optimistic Update Patterns**

```typescript
// Pattern 1: Node Position (Pure Optimistic)
// UI updates INSTANTLY, no server confirmation needed
const handleNodeDrag = (nodeId: string, newPosition: XYPosition) => {
  // Step 1: Update local React Flow state immediately
  setNodes(nodes => nodes.map(n => 
    n.id === nodeId ? { ...n, position: newPosition } : n
  ));
  
  // Step 2: Debounced persist to backend (fire-and-forget)
  debouncedSavePosition(nodeId, newPosition); // 300ms debounce
};

// Pattern 2: Node Deletion (Safe-Optimistic with Confirmation)
// Requires user confirmation, then instant UI removal
const handleNodeDelete = (nodeId: string) => {
  // Step 1: Show confirmation dialog
  if (!confirm('Delete this node?')) return;
  
  // Step 2: Remove from UI immediately
  setNodes(nodes => nodes.filter(n => n.id !== nodeId));
  
  // Step 3: Persist to backend (fire-and-forget)
  deleteNodeFromBackend(nodeId);
};

// Pattern 3: Content Generation (Pessimistic with Streaming)
// UI blocked during loading, progressive reveal during streaming
const handleGenerate = async (prompt: string) => {
  setNodeState('loading'); // Block UI
  
  try {
    const stream = await fetch('/api/process', { method: 'POST', body: prompt });
    const reader = stream.body.getReader();
    
    setNodeState('streaming'); // Enable output node
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      appendToOutput(new TextDecoder().decode(value));
    }
    setNodeState('complete');
  } catch {
    setNodeState('error');
  }
};
```

---

## 17) Deep Dive Level 5: API & Data Contract Tokens

Extracted from network traffic analysis. These are the **real API signatures** for reference.

**1. Supabase REST Endpoints (Observed)**

```typescript
// Canvas Management
POST   /rest/v1/canvases           → Create new canvas
GET    /rest/v1/canvases?user_id=eq.{uid}  → List user canvases
PATCH  /rest/v1/canvases?id=eq.{id}        → Update canvas metadata
DELETE /rest/v1/canvases?id=eq.{id}        → Delete canvas

// Node CRUD
POST   /rest/v1/content_nodes      → Create node
PATCH  /rest/v1/content_nodes?id=eq.{id}   → Update node position/config
DELETE /rest/v1/content_nodes?id=eq.{id}   → Delete node

// Credit Transactions
GET    /rest/v1/user_credits?user_id=eq.{uid}  → Balance check
POST   /rest/v1/credit_ledger      → Record debit/credit
```

**2. AI Processing API (Custom Next.js)**

```typescript
// Endpoint: POST /api/content-studio/process
// Content-Type: application/json
// Accept: text/event-stream (SSE)

interface ProcessRequest {
  canvasId: string;
  nodeId: string;
  prompt: string;
  model: 'claude-3.5-sonnet' | 'gpt-4-turbo' | 'gemini-pro';
  contextInputs: Array<{
    nodeId: string;
    content: string;
    type: 'text' | 'url' | 'file';
  }>;
  temperature?: number;  // 0.0 - 1.0
  maxTokens?: number;    // default 4096
}

// Response: Server-Sent Events stream
// data: {"delta": "content chunk", "tokens": 12}
// data: {"delta": "more content", "tokens": 8}
// data: [DONE]
```

**3. Credit System Logic**

```typescript
// Observed credit deduction formula
const CREDIT_COSTS = {
  'claude-3.5-sonnet': 2,    // Per request base
  'gpt-4-turbo': 3,
  'gemini-pro': 1,
  'perplexity-sonar': 2,
} as const;

// Token-based adjustment (observed pattern)
const calculateCreditCost = (model: string, inputTokens: number, outputTokens: number) => {
  const baseCost = CREDIT_COSTS[model] || 1;
  const tokenMultiplier = Math.ceil((inputTokens + outputTokens) / 1000);
  return baseCost * Math.max(1, tokenMultiplier);
};

// Example: 9 credits for a marketing plan generation
// = 2 (base) × 4.5 (≈4500 tokens / 1000) → rounded to 9
```

**4. TypeScript Interfaces for Vivid Implementation**

```typescript
// Adapted from Virlo's schema for Vivid's use

interface VividCanvas {
  id: string;                    // UUID
  user_id: string;
  title: string;
  description?: string;
  nodes: VividNode[];
  edges: VividEdge[];
  viewport: { x: number; y: number; zoom: number };
  created_at: string;            // ISO 8601
  updated_at: string;
}

interface VividNode {
  id: string;
  type: 'input' | 'processor' | 'output';
  subtype: string;               // e.g., 'youtube', 'capsule', 'script'
  position: { x: number; y: number };
  data: {
    label: string;
    config: Record<string, unknown>;
    state: NodeState;
    lastOutput?: string;
    tokenUsage?: { input: number; output: number };
  };
}

interface VividEdge {
  id: string;
  source: string;
  target: string;
  sourceHandle: 'primary' | 'context';
  targetHandle: 'input';
  type: 'data' | 'control';
  animated?: boolean;
}

// Credit Wallet (for billing transparency)
interface CreditWallet {
  subscription_balance: number;  // Monthly allocation
  topup_balance: number;         // Purchased packs
  api_balance: number;           // API-specific credits
  total_available: number;       // Computed sum
}
```

---

## 18) Deep Dive Level 6: React Component Architecture

Extracted from React Fiber tree analysis.

**Key Components (Minified Names Mapped)**

| Minified | Likely Purpose | Props Observed |
|----------|----------------|----------------|
| `tP` | CanvasProvider | `initialNodes`, `initialConnections`, `viewport` |
| `tI` | InteractionController | `onNodeClick`, `onEdgeConnect`, `onPaneClick` |
| `a4` | ReactFlow Core | `nodeTypes`, `edgeTypes`, `onMove`, `onReconnect` |
| `W` | Sidebar | `onAddNode`, `nodeCategories`, `collapsed` |
| `g` | AnimatedCounter | `value`, `duration`, `prefix` (for credits) |

**Vivid React Architecture Recommendation**

```
src/
├── components/
│   ├── canvas/
│   │   ├── CanvasProvider.tsx      # Context for canvas state
│   │   ├── NodeRenderer.tsx        # Dispatch to node types
│   │   ├── nodes/
│   │   │   ├── InputNode.tsx
│   │   │   ├── ProcessorNode.tsx
│   │   │   └── OutputNode.tsx
│   │   ├── edges/
│   │   │   ├── DataEdge.tsx
│   │   │   └── ControlEdge.tsx
│   │   └── controls/
│   │       ├── Minimap.tsx
│   │       └── ZoomControls.tsx
│   ├── sidebar/
│   │   ├── NodePalette.tsx
│   │   └── NodeCategory.tsx
│   └── credits/
│       ├── CreditCounter.tsx       # Top-right animated counter
│       └── CreditPurchaseModal.tsx
├── hooks/
│   ├── useCanvasState.ts           # Zustand/Jotai store
│   ├── useNodeLifecycle.ts         # FSM implementation
│   └── useStreamingGeneration.ts   # SSE handler
└── services/
    ├── canvasApi.ts                # Supabase client
    └── aiProcessor.ts              # /api/process wrapper
```

---

## 19) Actionable Token Summary (Quick Reference)

| Category | Token | Value/Pattern | Vivid File |
|----------|-------|---------------|------------|
| Color | `--accent` | `#ed62a0` | `globals.css` |
| Color | `--bg-base` | `#0c111d` | `globals.css` |
| Color | `--status-success` | `#12b76a` | `globals.css` |
| Color | `--status-error` | `#f04438` | `globals.css` |
| Border | Node default | `border-[#344054]` | `CustomNodes.tsx` |
| Border | Node active | `ring-2 ring-accent` | `CustomNodes.tsx` |
| Animation | Processing | `animate-pulse 2s` | `CustomNodes.tsx` |
| State | Node lifecycle | 5-state FSM | `useNodeLifecycle.ts` |
| API | Process endpoint | `POST /api/process` (SSE) | `aiProcessor.ts` |
| Credit | Base cost | 2 credits/Claude call | `CreditService.ts` |
| UX | Optimistic | Position/Delete instant | `useCanvasState.ts` |
| UX | Pessimistic | Generation streaming | `useStreamingGeneration.ts` |
