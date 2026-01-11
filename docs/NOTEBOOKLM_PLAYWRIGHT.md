# NotebookLM Playwright Automation Spec

> **Status**: Production  
> **Last Updated**: 2026-01-11  
> **Owner**: VDG Team

## Overview

`notebooklm_playwright.py` provides browser-based automation for NotebookLM operations (Create, Add Source, Query, Delete) using Chrome DevTools Protocol (CDP). This bypasses Google's TLS fingerprint blocking that rejects direct Python HTTP clients.

### Key Features (v2026.01.11)
- **RPC-First**: All operations attempt fast RPC calls first
- **UI Fallback**: Automatic fallback to UI interaction when RPC fails (HTTP 400)
- **Polling-based Wait**: Query response detected via message count polling (max 20s)
- **Consecutive Query Support**: Chat input cleared between queries

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Python Application                        │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │           PlaywrightNotebookLMClient                 │   │
│  │  • create_notebook()      → RPC → UI fallback       │   │
│  │  • add_text_source()      → RPC → UI fallback       │   │
│  │  • query()                → RPC → UI fallback       │   │
│  │  • delete_notebook()      → RPC → UI fallback       │   │
│  └─────────────────────────────────────────────────────┘   │
│                          │                                   │
│                          ▼                                   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │               Playwright CDP                         │   │
│  │        connect_over_cdp(localhost:9222)             │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                  Chrome Browser                              │
│           --remote-debugging-port=9222                       │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │            NotebookLM Tab (Authenticated)            │   │
│  │  • User logged into Google                          │   │
│  │  • Cookies valid                                    │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│               NotebookLM RPC Endpoints                       │
│           notebooklm.google.com/_/LabsTailwindUi             │
└─────────────────────────────────────────────────────────────┘
```

## RPC Reference

| RPC ID | Method | Parameters | Notes |
|--------|--------|------------|-------|
| `UVL1Se` | CreateNotebook | `[title]` | Returns notebook_id (UUID) |
| `bJmLpc` | AddSource | `[notebook_id, [[title, content, "text"]]]` | Returns source_id |
| `A0x2ad` | DeleteNotebook | `[[notebook_id]]` | Wrapped format required |
| `rLM1Ne` | GetNotebook | `[notebook_id, null, [2], null, 0]` | For source ID extraction |
| `GenerateFreeFormStreamed` | Query | `[sources_array, query, null, [2,null,[1]], conv_id]` | Streaming |

### Source Array Format
```javascript
// Per source: [[[source_id]]] (3 brackets)
sourceIds.map(sid => [[[sid]]])
```

## UI Fallback System

When RPC fails (e.g., HTTP 400 due to Google API changes), the client automatically falls back to UI interaction:

### Add Source UI Fallback
1. Navigate to notebook page
2. Press ESC to dismiss overlays
3. Click "Add source" button (`button[aria-label="Add source"]`)
4. Click "Copied text" option (multiple selectors tried)
5. Fill textarea in dialog (`[role="dialog"] textarea`)
6. Click "Insert" button
7. Verify source count increased

### Query UI Fallback
1. Count existing `.message-content` elements
2. Clear and fill chat textarea
3. Press Enter or click send button
4. **Polling loop** (1s interval, max 20s):
   - Check if message count increased by 2 (query + response)
   - Verify response > 50 chars and not "Loading..."
5. Fallback to `<p>` tag extraction if needed

## Prerequisites

1. **Chrome with Remote Debugging**
   ```bash
   /Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
     --remote-debugging-port=9222 \
     --user-data-dir=/tmp/chrome-debug
   ```

2. **Login to NotebookLM**
   - Navigate to https://notebooklm.google.com/
   - Complete Google login

3. **Install Playwright**
   ```bash
   pip install playwright
   ```

## API Reference

### PlaywrightNotebookLMClient

```python
class PlaywrightNotebookLMClient:
    def __init__(self, headless: bool = True, cdp_port: int = None): ...
    
    async def create_notebook(self, title: str) -> str:
        """Returns notebook_id. RPC first, then UI fallback."""
    
    async def add_text_source(self, notebook_id: str, title: str, content: str) -> Optional[str]:
        """Returns source_id or synthetic ID from UI fallback."""
    
    async def query(self, notebook_id: str, query_text: str, source_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        """Returns {answer: str, ...}. Uses polling-based UI fallback."""
    
    async def delete_notebook(self, notebook_id: str) -> bool:
        """RPC first, then UI fallback via menu."""
    
    async def close(self) -> None: ...
```

### Usage Pattern

```python
async with PlaywrightNotebookLMClient(cdp_port=9222) as client:
    # Create notebook
    nb_id = await client.create_notebook("Pattern Analysis")
    
    # Add source (returns ID or "ui_added_xxxxx" from fallback)
    source_id = await client.add_text_source(
        nb_id, 
        "Reference Document",
        "Content for grounded RAG..."
    )
    
    # Wait for indexing (NotebookLM needs time)
    await asyncio.sleep(10)
    
    # Query - uses polling, returns when response detected
    result = await client.query(
        nb_id, 
        "What are the key points?",
        source_ids=[source_id] if source_id else None
    )
    print(result["answer"])
    
    # Cleanup
    await client.delete_notebook(nb_id)
```

## Error Handling

### Common Issues & Solutions

| Error | Cause | Solution |
|-------|-------|----------|
| HTTP 400 on RPC | Google API changed | Automatic UI fallback |
| No answer from query | Response too short | UI fallback with polling |
| Cookie mismatch (401/403) | Direct HTTP blocked | Must use CDP connection |
| CSRF not found | Page not loaded | Navigate to NotebookLM first |
| Consecutive query fails | Input not cleared | Fixed: `clear()` before `fill()` |

### Logs to Watch

```
# Success patterns
[NotebookLM-Playwright] Created notebook via RPC: <uuid>
[NotebookLM-Playwright] Added source via UI: <title>
[NotebookLM-Playwright] Got answer via UI after 5s (250 chars)

# Fallback triggers
[NotebookLM-Playwright] RPC Add source failed: {...}. Trying UI fallback...
[NotebookLM-Playwright] RPC query returned no answer. Trying UI fallback...
```

## Testing

### Verification Script
```bash
python backend/scripts/verify_notebooklm_automation.py
```

### Expected Output
```
✅ Create Notebook: <uuid>
✅ Add Source: <source_uuid> or ui_added_xxxxx
✅ Query Success: Response Length XXXX
✅ Deleted notebook via RPC/UI
```

## File Structure

```
backend/app/rag/
├── notebooklm_playwright.py  # Core automation (this spec)
├── tier0_notebooklm.py       # High-level service layer
├── notebooklm_auth.py        # Auth tracking
├── semantic_cache.py         # Query caching with pgvector
└── artifact_storage.py       # Studio artifact storage

backend/scripts/
├── verify_notebooklm_automation.py  # E2E test
└── seed_rag_cache.py                # Pre-seed cache
```

## Changelog

### 2026-01-11
- Added polling-based query wait (max 20s, 1s interval)
- Added consecutive query support (clear input before fill)
- Improved UI fallback for add_text_source with multi-selector approach
- Added message count comparison for response detection
- Removed fixed `asyncio.sleep(15)` in favor of polling

### 2026-01-08
- Initial production release
- RPC-based operations with basic UI fallback

## Related Files
- [tier0_notebooklm.py](file:///Users/ted/vivid/backend/app/rag/tier0_notebooklm.py) - Service layer with MCP/Playwright fallback
- [semantic_cache.py](file:///Users/ted/vivid/backend/app/rag/semantic_cache.py) - Query result caching
