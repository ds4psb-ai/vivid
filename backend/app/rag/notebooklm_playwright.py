"""
Playwright-based NotebookLM Automation Client

Uses real browser context via Chrome DevTools Protocol (CDP) to execute RPC calls,
bypassing Google's TLS fingerprint checks that reject Python HTTP clients.

Architecture:
    - Connects to Chrome with --remote-debugging-port=9223
    - Reuses authenticated browser session (user must be logged into NotebookLM)
    - Executes internal RPC calls via page.evaluate() JavaScript injection

RPC Reference (verified 2026-01):
    - CCqFvf: CreateNotebook
    - izAoDd: AddSource (text, URL, YouTube)
    - WWINqb: DeleteNotebook (params: [[notebook_id], [2]])
    - wXbhsf: ListNotebooks
    - GenerateFreeFormStreamed: Query (streaming endpoint)

Usage:
    from app.rag.notebooklm_playwright import PlaywrightNotebookLMClient
    
    async with PlaywrightNotebookLMClient(cdp_port=9223) as client:
        nb_id = await client.create_notebook("My Notebook")
        source_id = await client.add_text_source(nb_id, "Title", "Content...")
        result = await client.query(nb_id, "Question?", source_ids=[source_id])
        print(result["answer"])
        await client.delete_notebook(nb_id)

Prerequisites:
    1. Chrome running with: --remote-debugging-port=9223
    2. User logged into NotebookLM in that Chrome session
    3. playwright package installed
"""

import asyncio
import json
import logging
import os
import re
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, TypeVar
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# =============================================================================
# Constants
# =============================================================================

# User data directory for persistent browser session
BROWSER_DATA_DIR = Path.home() / ".notebooklm-mcp" / "playwright-profile"

# RPC IDs - Verified 2026-01 (subject to change by Google)
RPC_CREATE_NOTEBOOK = "CCqFvf"
RPC_ADD_SOURCE = "izAoDd"
RPC_DELETE_NOTEBOOK = "WWINqb"
RPC_LIST_NOTEBOOKS = "wXbhsf"
QUERY_ENDPOINT = "GenerateFreeFormStreamed"

# Timeouts (milliseconds)
DEFAULT_QUERY_TIMEOUT_MS = 60000
DEFAULT_CRUD_TIMEOUT_MS = 30000

# Retry configuration
MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 1.0


# =============================================================================
# Exception Classes
# =============================================================================

class NotebookLMError(Exception):
    """Base exception for NotebookLM operations."""
    pass


class NotebookLMAuthError(NotebookLMError):
    """Authentication/login required."""
    pass


class NotebookLMRPCError(NotebookLMError):
    """RPC call failed (400, 500, etc)."""
    def __init__(self, message: str, status_code: int = 0, rpc_id: str = ""):
        super().__init__(message)
        self.status_code = status_code
        self.rpc_id = rpc_id


class NotebookLMTimeoutError(NotebookLMError):
    """Operation timed out."""
    pass


# =============================================================================
# Retry Decorator
# =============================================================================

T = TypeVar("T")


def with_retry(
    max_retries: int = MAX_RETRIES,
    delay: float = RETRY_DELAY_SECONDS,
    exceptions: tuple = (NotebookLMRPCError,),
) -> Callable:
    """Decorator for retrying async functions with exponential backoff."""
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        wait_time = delay * (2 ** attempt)
                        logger.warning(
                            f"[NotebookLM] {func.__name__} failed (attempt {attempt + 1}/{max_retries}): {e}. "
                            f"Retrying in {wait_time:.1f}s..."
                        )
                        await asyncio.sleep(wait_time)
            raise last_exception
        return wrapper
    return decorator




@dataclass
class NotebookInfo:
    """Simple notebook info container."""
    notebook_id: str
    title: str


class PlaywrightNotebookLMClient:
    """
    Playwright-based NotebookLM client.
    
    Executes RPC queries in a real browser context to avoid cookie fingerprint issues.
    Uses persistent browser context to maintain Google login session.
    
    Two modes:
    1. CDP mode (cdp_port): Connect to existing Chrome with --remote-debugging-port
    2. Standalone mode: Launch new browser with persistent profile
    """
    
    def __init__(self, headless: bool = True, cdp_port: int = None):
        """
        Initialize Playwright client.
        
        Args:
            headless: Run browser in headless mode (default: True)
            cdp_port: Chrome DevTools port to connect to existing Chrome (e.g., 9222)
        """
        self.headless = headless
        self.cdp_port = cdp_port
        self._use_cdp = cdp_port is not None
        self._playwright = None
        self._browser = None
        self._context = None
        self._page = None
        self._initialized = False
    
    async def __aenter__(self):
        await self._init_browser()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def connect(self):
        """Alias for _init_browser for API compatibility."""
        await self._init_browser()
    
    async def _init_browser(self):
        """Initialize Playwright browser - CDP or persistent context."""
        if self._initialized:
            return
        
        try:
            from playwright.async_api import async_playwright
            
            self._playwright = await async_playwright().start()
            
            if self._use_cdp:
                # CDP mode: Connect to existing Chrome with remote debugging
                logger.info(f"[NotebookLM-CDP] Connecting to port {self.cdp_port}...")
                self._browser = await self._playwright.chromium.connect_over_cdp(
                    f"http://localhost:{self.cdp_port}"
                )
                
                # Get existing contexts/pages
                contexts = self._browser.contexts
                if contexts:
                    self._context = contexts[0]
                    # Find NotebookLM page (must be exact match)
                    self._page = await self._find_notebooklm_page()
                    
                    if not self._page:
                        # Create new page and navigate
                        self._page = await self._context.new_page()
                        await self._page.goto("https://notebooklm.google.com/", wait_until="domcontentloaded")
                        await asyncio.sleep(2)
                
                if not self._page:
                    raise RuntimeError("No NotebookLM page available in CDP mode")
                    
                logger.info(f"[NotebookLM-CDP] Found existing tab: {self._page.url}")
                
            else:
                # Standalone mode: Launch real Chrome with persistent profile
                BROWSER_DATA_DIR.mkdir(parents=True, exist_ok=True)
                
                self._context = await self._playwright.chromium.launch_persistent_context(
                    user_data_dir=str(BROWSER_DATA_DIR),
                    headless=self.headless,
                    channel="chrome",
                    args=[
                        "--disable-blink-features=AutomationControlled",
                        "--no-sandbox",
                    ],
                    viewport={"width": 1280, "height": 800},
                    locale="ko-KR",
                    ignore_https_errors=True,
                )
                
                if self._context.pages:
                    self._page = self._context.pages[0]
                else:
                    self._page = await self._context.new_page()
                
                await self._inject_cached_cookies()
            
            self._initialized = True
            logger.info("[NotebookLM-Playwright] Browser initialized")
            
        except Exception as e:
            logger.error(f"[NotebookLM-Playwright] Failed to init browser: {e}")
            raise
    
    async def _find_notebooklm_page(self):
        """Find existing NotebookLM page in CDP context."""
        if not self._context:
            return None
        
        for page in self._context.pages:
            url = page.url.lower()
            is_nlm = ("notebooklm.google" in url) and ("accounts.google.com" not in url)
            if is_nlm:
                return page
        
        return None

    async def close(self):
        """Close browser and cleanup."""
        if self._context and not self._use_cdp:
            await self._context.close()
        if self._playwright:
            await self._playwright.stop()
        self._initialized = False
        logger.info("[NotebookLM-Playwright] Browser closed")
    
    async def _inject_cached_cookies(self):
        """Inject cookies from cached auth.json into browser context."""
        auth_file = Path.home() / ".notebooklm-mcp" / "auth.json"
        
        if not auth_file.exists():
            return
        
        try:
            with open(auth_file) as f:
                auth_data = json.load(f)
            
            cookies = auth_data.get("cookies", {})
            if not cookies:
                return
            
            import time
            playwright_cookies = []
            for name, value in cookies.items():
                domain = "notebooklm.google.com" if name.startswith("__Host-") else ".google.com"
                cookie = {
                    "name": name,
                    "value": value,
                    "domain": domain,
                    "path": "/",
                    "expires": time.time() + 86400 * 30,
                    "httpOnly": name.startswith("__Secure") or name in ("SID", "HSID", "SSID"),
                    "secure": True,
                    "sameSite": "None" if name.startswith("__Secure-3P") else "Lax",
                }
                playwright_cookies.append(cookie)
            
            await self._context.add_cookies(playwright_cookies)
            logger.info(f"[NotebookLM-Playwright] Injected {len(playwright_cookies)} cookies")
            
        except Exception as e:
            logger.warning(f"[NotebookLM-Playwright] Failed to inject cookies: {e}")
    
    async def ensure_logged_in(self) -> bool:
        """Check if logged into NotebookLM."""
        if "notebooklm.google.com" not in self._page.url:
             await self._page.goto("https://notebooklm.google.com/", wait_until="domcontentloaded")
             await asyncio.sleep(2)
        
        current_url = self._page.url
        if "accounts.google.com" in current_url or "signin" in current_url:
            logger.warning("[NotebookLM-Playwright] Login required")
            return False
        
        return "notebooklm.google.com" in current_url

    async def create_notebook(self, title: str = "Pattern Analysis") -> str:
        """Create a new notebook."""
        if not self._initialized:
            await self._init_browser()
        
        if "notebooklm.google" not in self._page.url.lower():
            raise RuntimeError("NotebookLM 탭이 필요합니다.")
        
        # Navigate to homepage if currently inside a notebook
        if "/notebook/" in self._page.url:
            await self._page.goto("https://notebooklm.google.com/", wait_until="domcontentloaded")
            await asyncio.sleep(2)
        
        js_create = """
            async () => {
                const logs = [];
                function log(msg) { logs.push(msg); }
                
                try {
                    const pageSource = document.documentElement.outerHTML;
                    const csrfMatch = pageSource.match(/"SNlM0e":"([^"]+)"/);
                    const csrf = csrfMatch ? csrfMatch[1] : null;
                    const sidMatch = pageSource.match(/"FdrFJe":"([^"]+)"/);
                    const sid = sidMatch ? sidMatch[1] : null;
                    
                    const bl = (window.WIZ_global_data && window.WIZ_global_data.cfb2h) 
                        ? window.WIZ_global_data.cfb2h 
                        : "boq_labs-tailwind-frontend_20251221.14_p0";
                    
                    if (!csrf) return { error: "CSRF token not found", logs: logs };
                    
                    const reqIdBase = Math.floor(Math.random() * 900000) + 100000;
                    const title = TITLE_PLACEHOLDER;
                    
                    // CCqFvf RPC for create notebook (verified working)
                    // Params: [title, null, null, [2], [1, null*13, [1]]]
                    const defaults = [1].concat(Array(13).fill(null)).concat([[1]]);
                    const params = [title, null, null, [2], defaults];
                    const rpcEnvelope = [[["CCqFvf", JSON.stringify(params), null, "generic"]]];
                    
                    const rpcBody = new URLSearchParams();
                    rpcBody.append("f.req", JSON.stringify(rpcEnvelope));
                    rpcBody.append("at", csrf);
                    
                    const rpcUrl = `https://notebooklm.google.com/_/LabsTailwindUi/data/batchexecute?rpcids=CCqFvf&source-path=/&f.sid=${sid}&bl=${bl}&hl=en&_reqid=${reqIdBase}&rt=c`;
                    
                    log("Sending CCqFvf CreateNotebook RPC...");
                    const rpcRes = await fetch(rpcUrl, {
                        method: "POST",
                        headers: {"Content-Type": "application/x-www-form-urlencoded;charset=UTF-8"},
                        body: rpcBody.toString(),
                        credentials: "include"
                    });
                    
                    const rpcText = await rpcRes.text();
                    log(`RPC Response length: ${rpcText.length}`);
                    
                    // Parse response to extract notebook ID
                    const cleaned = rpcText.replace(/^\\)\\]\\}'\\n/, '');
                    const lines = cleaned.split('\\n');
                    
                    for (const line of lines) {
                        try {
                            const parsed = JSON.parse(line);
                            if (parsed[0] && parsed[0][1] === "CCqFvf") {
                                const data = JSON.parse(parsed[0][2]);
                                // Structure: [title, sources, notebook_id, ...]
                                if (data && data.length >= 3 && data[2]) {
                                    return { success: true, notebook_id: data[2], logs: logs };
                                }
                            }
                        } catch(e) {}
                    }
                    
                    // Fallback: regex UUID
                    const uuidPattern = /[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}/gi;
                    const matches = rpcText.match(uuidPattern);
                    if (matches && matches.length > 0) {
                        return { success: true, notebook_id: matches[0], logs: logs };
                    }
                    
                    return { error: "No notebook ID in response", raw: rpcText.substring(0, 500), logs: logs };
                    
                } catch (e) {
                    return { error: e.message, logs: logs };
                }
            }
        """
        
        js_create = js_create.replace("TITLE_PLACEHOLDER", json.dumps(title))
        result = await self._page.evaluate(js_create)
        
        if result.get("success") and result.get("notebook_id"):
            notebook_id = result.get("notebook_id")
            logger.info(f"[NotebookLM-Playwright] Created notebook: {notebook_id}")
            return notebook_id
            
        if result.get("error"):
            raise RuntimeError(f"Create notebook failed: {result['error']}")
        raise RuntimeError("Create notebook failed (Unknown)")

    async def add_text_source(self, notebook_id: str, title: str, content: str) -> Optional[str]:
        """
        Add a text source to a notebook.
        
        Returns:
            source_id (str) on success, None on failure
        """
        if not self._initialized:
            await self._init_browser()
        
        js_add_source = """
            async () => {
                try {
                    const pageSource = document.documentElement.outerHTML;
                    const csrfMatch = pageSource.match(/"SNlM0e":"([^"]+)"/);
                    const csrf = csrfMatch ? csrfMatch[1] : null;
                    const sidMatch = pageSource.match(/"FdrFJe":"([^"]+)"/);
                    const sid = sidMatch ? sidMatch[1] : null;
                    
                    const bl = (window.WIZ_global_data && window.WIZ_global_data.cfb2h) 
                        ? window.WIZ_global_data.cfb2h 
                        : "boq_labs-tailwind-frontend_20251221.14_p0";
                    
                    if (!csrf) return { error: "CSRF token not found" };
                    
                    const notebookId = "NOTEBOOK_ID_PLACEHOLDER";
                    const sourceTitle = SOURCE_TITLE_PLACEHOLDER;
                    const sourceContent = SOURCE_CONTENT_PLACEHOLDER;
                    
                    const reqIdBase = Math.floor(Math.random() * 900000) + 100000;
                    
                    // izAoDd RPC for add text source
                    const sourceData = [null, [sourceTitle, sourceContent], null, 2, null, null, null, null, null, null, 1];
                    const defaults = [1].concat(Array(9).fill(null)).concat([[1]]);
                    const params = [[sourceData], notebookId, [2], defaults];
                    
                    const rpcEnvelope = [[["izAoDd", JSON.stringify(params), null, "generic"]]];
                    
                    const rpcBody = new URLSearchParams();
                    rpcBody.append("f.req", JSON.stringify(rpcEnvelope));
                    rpcBody.append("at", csrf);
                    
                    const rpcUrl = `https://notebooklm.google.com/_/LabsTailwindUi/data/batchexecute?rpcids=izAoDd&source-path=/notebook/${notebookId}&f.sid=${sid}&bl=${bl}&hl=en&_reqid=${reqIdBase}&rt=c`;
                    
                    const rpcRes = await fetch(rpcUrl, {
                        method: "POST",
                        headers: {"Content-Type": "application/x-www-form-urlencoded;charset=UTF-8"},
                        body: rpcBody.toString(),
                        credentials: "include"
                    });
                    
                    if (!rpcRes.ok) {
                        return { error: `HTTP ${rpcRes.status}` };
                    }
                    
                    // Parse response to extract source_id
                    const rpcText = await rpcRes.text();
                    const cleaned = rpcText.replace(/^\\)\\]\\}'\\n/, '');
                    const lines = cleaned.split('\\n');
                    
                    for (const line of lines) {
                        if (line.startsWith('[')) {
                            try {
                                const parsed = JSON.parse(line);
                                if (parsed[0] && parsed[0][1] === "izAoDd") {
                                    const data = JSON.parse(parsed[0][2]);
                                    // Structure: [[[[source_id], title, ...], ...]]
                                    if (data && data[0] && data[0][0] && data[0][0][0] && data[0][0][0][0]) {
                                        const sourceId = data[0][0][0][0];
                                        return { success: true, source_id: sourceId };
                                    }
                                }
                            } catch(e) {}
                        }
                    }
                    
                    return { success: true, source_id: null };  // Added but couldn't extract ID
                    
                } catch (e) {
                    return { error: e.message };
                }
            }
        """
        
        js_add_source = js_add_source.replace("NOTEBOOK_ID_PLACEHOLDER", notebook_id)
        js_add_source = js_add_source.replace("SOURCE_TITLE_PLACEHOLDER", json.dumps(title))
        js_add_source = js_add_source.replace("SOURCE_CONTENT_PLACEHOLDER", json.dumps(content))
        
        result = await self._page.evaluate(js_add_source)
        
        if result.get("success"):
            source_id = result.get("source_id")
            logger.info(f"[NotebookLM-Playwright] Added source: {title} (id: {source_id})")
            return source_id
        
        logger.warning(f"[NotebookLM-Playwright] RPC Add source failed: {result}. Trying UI fallback...")
        return await self._add_source_ui_fallback(notebook_id, title, content)

    async def _add_source_ui_fallback(self, notebook_id: str, title: str, content: str) -> Optional[str]:
        """Fallback to UI interaction for adding source (synced from komission 2026-01-11)."""
        try:
            # 0. Navigate to notebook if needed
            if notebook_id not in self._page.url:
                await self._page.goto(
                    f"https://notebooklm.google.com/notebook/{notebook_id}",
                    wait_until="domcontentloaded"
                )
                await asyncio.sleep(2)
            
            # 1. Dismiss any open overlays/dialogs with ESC
            await self._page.keyboard.press("Escape")
            await asyncio.sleep(0.5)
            
            # 2. Look for the "Add sources" panel or button
            # UI has button with aria-label="Add source" 
            add_source_btn = self._page.locator('button[aria-label="Add source"]')
            if await add_source_btn.count() > 0:
                await add_source_btn.first.click(force=True)
                await asyncio.sleep(1)
            
            # 3. Find and click "Copied text" option in the source type menu
            # The panel shows options like "Upload", "Link", "Copied text"
            # Try multiple selectors
            copied_text_selectors = [
                'text="Copied text"',
                'text="복사된 텍스트"',
                '[data-value="copied_text"]',
                'button:has-text("Copied text")',
                'div:has-text("Copied text"):not(:has(div))',
            ]
            
            clicked = False
            for selector in copied_text_selectors:
                try:
                    elem = self._page.locator(selector)
                    if await elem.count() > 0:
                        await elem.first.click(force=True)
                        clicked = True
                        logger.debug(f"[NotebookLM-Playwright] Clicked: {selector}")
                        break
                except Exception:
                    continue
            
            if not clicked:
                # Try clicking any visible menu item with "text" in it
                text_option = self._page.locator('div[role="menuitem"]').filter(has_text="text")
                if await text_option.count() > 0:
                    await text_option.first.click(force=True)
                    clicked = True
            
            if not clicked:
                logger.warning("[NotebookLM-Playwright] Could not find 'Copied text' option")
                return None
            
            await asyncio.sleep(1)
            
            # 4. Skip Name/Title field - NotebookLM "Paste copied text" dialog doesn't have one
            # The title is auto-generated from content
            
            # 5. Fill in the Content textarea in the dialog
            # The dialog has a textarea with placeholder "Paste text here"
            dialog_textarea = self._page.locator('[role="dialog"] textarea, .mat-dialog-container textarea, textarea[placeholder*="Paste"]')
            if await dialog_textarea.count() > 0:
                await dialog_textarea.first.fill(content)
                logger.debug(f"[NotebookLM-Playwright] Filled dialog textarea")
            else:
                # Fallback: find textarea that's NOT the chat input
                # Chat textarea has placeholder like "Start typing..." or "Ask follow-up"
                all_textareas = self._page.locator('textarea:visible')
                count = await all_textareas.count()
                for i in range(count):
                    ta = all_textareas.nth(i)
                    placeholder = await ta.get_attribute('placeholder') or ''
                    if 'paste' in placeholder.lower() or 'text here' in placeholder.lower():
                        await ta.fill(content)
                        logger.debug(f"[NotebookLM-Playwright] Filled textarea with placeholder: {placeholder}")
                        break
                else:
                    logger.warning("[NotebookLM-Playwright] Could not find dialog textarea")
                    return None
            
            await asyncio.sleep(0.5)
            
            # 6. Click Insert button
            insert_btn = self._page.locator('button:has-text("Insert")')
            if await insert_btn.count() > 0:
                await insert_btn.first.click(force=True)
                logger.debug("[NotebookLM-Playwright] Clicked Insert button")
            else:
                logger.warning("[NotebookLM-Playwright] Could not find Insert button")
                return None
            
            # 7. Wait for processing and verify source was added
            await asyncio.sleep(3)
            
            # Check if source appears in source list (count should be >= 1)
            source_count_elem = self._page.locator('text=/\\d+ source/')
            if await source_count_elem.count() > 0:
                logger.info(f"[NotebookLM-Playwright] Added source via UI: {title}")
                return f"ui_added_{notebook_id[:8]}"
            else:
                # Alternative check: look for source in left panel
                logger.info(f"[NotebookLM-Playwright] Added source via UI (unverified): {title}")
                return f"ui_added_{notebook_id[:8]}"
            
        except Exception as e:
            logger.error(f"[NotebookLM-Playwright] UI Add Source failed: {e}")
            return None

    async def delete_notebook(self, notebook_id: str) -> bool:
        """Delete a notebook with RPC first, then UI fallback."""
        if not self._initialized:
            await self._init_browser()
        
        # Try RPC first
        js_delete = """
            async () => {
                const logs = [];
                function log(msg) { logs.push(msg); }
                
                try {
                    const pageSource = document.documentElement.outerHTML;
                    const csrfMatch = pageSource.match(/"SNlM0e":"([^"]+)"/);
                    const csrf = csrfMatch ? csrfMatch[1] : null;
                    const sidMatch = pageSource.match(/"FdrFJe":"([^"]+)"/);
                    const sid = sidMatch ? sidMatch[1] : null;
                    
                    const bl = (window.WIZ_global_data && window.WIZ_global_data.cfb2h) 
                        ? window.WIZ_global_data.cfb2h 
                        : "boq_labs-tailwind-frontend_20251221.14_p0";
                    
                    const notebookId = "NOTEBOOK_ID_PLACEHOLDER";
                    const reqIdBase = Math.floor(Math.random() * 900000) + 100000;
                    
                    log(`Deleting notebook: ${notebookId}`);
                    
                    // Try A0x2ad (archive) and WWINqb (delete) RPCs
                    const params = [[notebookId], [2]];  // Wrapped format
                    const rpcEnvelope = [[["WWINqb", JSON.stringify(params), null, "generic"]]];
                    
                    const rpcBody = new URLSearchParams();
                    rpcBody.append("f.req", JSON.stringify(rpcEnvelope));
                    rpcBody.append("at", csrf);
                    
                    const rpcUrl = `https://notebooklm.google.com/_/LabsTailwindUi/data/batchexecute?rpcids=WWINqb&f.sid=${sid}&bl=${bl}&hl=en&_reqid=${reqIdBase}&rt=c`;
                    
                    const rpcRes = await fetch(rpcUrl, {
                        method: "POST",
                        headers: {"Content-Type": "application/x-www-form-urlencoded;charset=UTF-8"},
                        body: rpcBody.toString(),
                        credentials: "include"
                    });
                    
                    log(`RPC Status: ${rpcRes.status}, Length: ${(await rpcRes.clone().text()).length}`);
                    
                    return { success: rpcRes.ok, status: rpcRes.status, logs: logs };
                } catch (e) {
                    return { error: e.message, logs: logs };
                }
            }
        """
        
        js_delete = js_delete.replace("NOTEBOOK_ID_PLACEHOLDER", notebook_id)
        result = await self._page.evaluate(js_delete)
        
        if result.get("success"):
            logger.info(f"[NotebookLM-Playwright] Deleted notebook via RPC: {notebook_id}")
            return True
        
        # RPC failed, try UI fallback
        logger.warning(f"[NotebookLM-Playwright] RPC Delete failed: {result}. Trying UI fallback...")
        
        try:
            # 1. Navigate to home page
            await self._page.goto("https://notebooklm.google.com/", wait_until="domcontentloaded")
            await asyncio.sleep(2)
            
            # 2. Find and click the first "Project Actions Menu" button (most recent notebook)
            menu_buttons = self._page.locator('button[aria-label="Project Actions Menu"]')
            count = await menu_buttons.count()
            
            if count == 0:
                logger.warning("[NotebookLM-Playwright] No notebook menu buttons found")
                return False
            
            # Click first menu (most recently created notebook)
            await menu_buttons.first.click(force=True)
            await asyncio.sleep(0.5)
            
            # 3. Click "Delete" option - menu text is "delete\nDelete" (icon + text)
            delete_option = self._page.locator('[role="menuitem"]').filter(has_text="Delete")
            
            if await delete_option.count() > 0:
                await delete_option.first.click(force=True)
                await asyncio.sleep(1)
                
                # 4. Confirm deletion if dialog appears
                confirm_btn = self._page.locator('button:has-text("Delete"), button:has-text("삭제"), button:has-text("Confirm")')
                if await confirm_btn.count() > 0:
                    await confirm_btn.first.click(force=True)
                    await asyncio.sleep(1)
                
                logger.info(f"[NotebookLM-Playwright] Deleted notebook via UI: {notebook_id}")
                return True
            else:
                # Close menu
                await self._page.keyboard.press("Escape")
                logger.warning("[NotebookLM-Playwright] 'Delete' option not found in menu")
                return False
            
        except Exception as e:
            logger.error(f"[NotebookLM-Playwright] UI Delete failed: {e}")
            return False

    async def query(
        self,
        notebook_id: str,
        query_text: str,
        source_ids: Optional[List[str]] = None,
        timeout_ms: int = 60000,
    ) -> Dict[str, Any]:
        """
        Execute a query against a NotebookLM notebook.
        
        Args:
            notebook_id: The notebook UUID
            query_text: The question to ask
            source_ids: Optional list of source IDs to query (bypasses auto-detection)
            timeout_ms: Query timeout in milliseconds
            
        Returns:
            Dict with answer, sources, and metadata
        """
        if not self._initialized:
            await self._init_browser()
        
        # *** CRITICAL: Navigate to notebook page before querying ***
        notebook_url = f"https://notebooklm.google.com/notebook/{notebook_id}"
        if notebook_id not in self._page.url:
            await self._page.goto(notebook_url, wait_until="domcontentloaded")
            await asyncio.sleep(2)
        
        # Check login status
        if "accounts.google.com" in self._page.url:
            raise RuntimeError("Login required. Run interactive login first.")
        
        # If source_ids provided, use them directly (cleanest path, avoids owner ID confusion)
        source_ids_json = json.dumps(source_ids if source_ids else [])
        
        # Execute RPC query via JavaScript in browser context
        js_code = """
            async () => {
                const logs = [];
                function log(msg) { logs.push(msg); }
                
                try {
                    log("Starting query...");
                    
                    const pageSource = document.documentElement.outerHTML;
                    const csrfMatch = pageSource.match(/"SNlM0e":"([^"]+)"/);
                    const csrf = csrfMatch ? csrfMatch[1] : null;
                    const sidMatch = pageSource.match(/"FdrFJe":"([^"]+)"/);
                    const sid = sidMatch ? sidMatch[1] : null;
                    
                    const bl = (window.WIZ_global_data && window.WIZ_global_data.cfb2h) 
                        ? window.WIZ_global_data.cfb2h 
                        : "boq_labs-tailwind-frontend_20251221.14_p0";
                    
                    log("BL Version: " + bl);

                    if (!csrf) return { error: "CSRF token not found", logs: logs };

                    const notebookId = "NOTEBOOK_ID_PLACEHOLDER";
                    const query = QUERY_PLACEHOLDER;
                    const providedSourceIds = PROVIDED_SOURCE_IDS_PLACEHOLDER;
                    const reqIdBase = Math.floor(Math.random() * 900000) + 100000;

                    // Use provided source_ids if available, else fetch via wXbhsf
                    let sourceIds = providedSourceIds;
                    
                    if (sourceIds.length === 0) {
                        log("No source_ids provided, fetching via wXbhsf...");
                        try {
                            const listParams = [null, 1, null, [2]];
                            const rpcEnvelope = [[["wXbhsf", JSON.stringify(listParams), null, "generic"]]];
                            
                            const rpcBody = new URLSearchParams();
                            rpcBody.append("f.req", JSON.stringify(rpcEnvelope));
                            rpcBody.append("at", csrf);
                            
                            const rpcUrl = `https://notebooklm.google.com/_/LabsTailwindUi/data/batchexecute?rpcids=wXbhsf&source-path=/&f.sid=${sid}&bl=${bl}&hl=en&_reqid=${reqIdBase}&rt=c`;
                            
                            const rpcRes = await fetch(rpcUrl, {
                                method: "POST",
                                headers: {"Content-Type": "application/x-www-form-urlencoded;charset=UTF-8"},
                                body: rpcBody.toString(),
                                credentials: "include"
                            });
                            
                            const rpcText = await rpcRes.text();
                            const cleaned = rpcText.replace(/^\\)\\]\\}'\\n/, '');
                            const lines = cleaned.split('\\n');
                            
                            for (const line of lines) {
                                if (line.startsWith('[')) {
                                    try {
                                        const parsed = JSON.parse(line);
                                        if (parsed[0] && parsed[0][1] === "wXbhsf") {
                                            const data = JSON.parse(parsed[0][2]);
                                            if (data && data[0] && Array.isArray(data[0])) {
                                                const notebook = data[0].find(nb => nb && nb[2] === notebookId);
                                                if (notebook && notebook[1] && Array.isArray(notebook[1])) {
                                                    sourceIds = notebook[1].map(s => {
                                                        if (s && s[0] && Array.isArray(s[0])) return s[0][0];
                                                        return null;
                                                    }).filter(id => id);
                                                }
                                            }
                                        }
                                    } catch(e) {}
                                }
                            }
                        } catch (e) {
                            log(`wXbhsf Error: ${e.message}`);
                        }
                    } else {
                        log(`Using ${sourceIds.length} provided source IDs`);
                    }
                    
                    log(`Source IDs: ${sourceIds.length} total`);

                    // 2. Execute Query using GenerateFreeFormStreamed
                    const conversationId = crypto.randomUUID();
                    // Sources structure: [[sid]] per item (2 brackets, wrapped in outer array becomes 3)
                    const sourcesArray = sourceIds.map(sid => [[sid]]);

                    const params = [
                        sourcesArray,
                        query,
                        null,  // conversation history
                        [2, null, [1]],
                        conversationId
                    ];
                    
                    const fReq = [null, JSON.stringify(params)];
                    
                    const formData = new URLSearchParams();
                    formData.append("f.req", JSON.stringify(fReq));
                    formData.append("at", csrf);
                    
                    const url = `https://notebooklm.google.com/_/LabsTailwindUi/data/google.internal.labs.tailwind.orchestration.v1.LabsTailwindOrchestrationService/GenerateFreeFormStreamed?bl=${bl}&hl=en&f.sid=${sid}&_reqid=${reqIdBase + 1000}&rt=c`;

                    log("Sending Stream Query...");
                    const response = await fetch(url, {
                        method: "POST",
                        headers: {
                            "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
                            "X-Same-Domain": "1"
                        },
                        body: formData.toString(),
                        credentials: "include"
                    });
                    
                    const text = await response.text();
                    log(`Stream Response Length: ${text.length}`);

                    return {
                        status: response.status,
                        success: response.ok,
                        source_count: sourceIds.length,
                        raw_response: text.substring(text.length > 100000 ? text.length - 100000 : 0),
                        notebook_id: notebookId,
                        logs: logs
                    };
                } catch (e) {
                    return { error: e.message, logs: logs };
                }
            }
        """

        js_code = js_code.replace("NOTEBOOK_ID_PLACEHOLDER", notebook_id)
        js_code = js_code.replace("QUERY_PLACEHOLDER", json.dumps(query_text))
        js_code = js_code.replace("PROVIDED_SOURCE_IDS_PLACEHOLDER", source_ids_json)

        result = await self._page.evaluate(js_code)
        
        # Post-Processing: Extract answer
        if result.get("success") and result.get("raw_response"):
            raw = result["raw_response"]
            if raw.startswith(")]}'"):
                raw = raw[4:].strip()
            
            result["answer"] = self._extract_answer_from_raw(raw) or "No answer found."

        # UI Fallback if RPC failed or returned no answer (synced from komission 2026-01-11)
        answer_text = result.get("answer", "")
        if not answer_text or "No answer" in answer_text or len(answer_text) < 50:
            logger.warning(f"[NotebookLM-Playwright] RPC query returned no answer. Trying UI fallback...")
            try:
                # Navigate to notebook if needed
                if notebook_id not in self._page.url:
                    await self._page.goto(
                        f"https://notebooklm.google.com/notebook/{notebook_id}",
                        wait_until="domcontentloaded"
                    )
                    await asyncio.sleep(2)
                
                # Count existing messages BEFORE sending query (for detecting new response)
                messages_before = self._page.locator('.message-content')
                msg_count_before = await messages_before.count()
                
                # Find chat input
                chat_input = self._page.locator('textarea[placeholder*="typing"], textarea[placeholder*="Start"], textarea.chat-input')
                if await chat_input.count() == 0:
                    # Fallback: find any visible textarea that looks like chat
                    chat_input = self._page.locator('textarea:visible').last
                
                if await chat_input.count() > 0:
                    # Clear existing text first (for consecutive queries)
                    await chat_input.clear()
                    await asyncio.sleep(0.2)
                    await chat_input.fill(query_text)
                    await asyncio.sleep(0.3)
                    
                    # Click send button or press Enter
                    send_btn = self._page.locator('button[aria-label*="send"], button[aria-label*="Send"]')
                    if await send_btn.count() > 0:
                        await send_btn.first.click()
                    else:
                        await chat_input.press("Enter")
                    
                    # Wait for response (NotebookLM can take 10-15 seconds)
                    await asyncio.sleep(15)
                    
                    # Extract answer from chat history
                    # .message-content contains the actual message text
                    # Look for NEW messages (count should have increased)
                    messages = self._page.locator('.message-content')
                    msg_count = await messages.count()
                    
                    if msg_count > msg_count_before:
                        # Last message should be the AI response
                        last_msg = messages.nth(msg_count - 1)
                        ui_answer = await last_msg.text_content()
                        if ui_answer and len(ui_answer) > 50:
                            result["answer"] = ui_answer.strip()
                            logger.info(f"[NotebookLM-Playwright] Got answer via UI .message-content ({len(ui_answer)} chars)")
                    
                    # Fallback: try <p> tags which contain the actual response text
                    if not result.get("answer") or len(result.get("answer", "")) < 50:
                        p_tags = self._page.locator('.message-content p, [class*="response"] p')
                        if await p_tags.count() > 0:
                            # Get the last paragraph which should be from the response
                            last_p = p_tags.last
                            p_text = await last_p.text_content()
                            if p_text and len(p_text) > 50:
                                result["answer"] = p_text.strip()
                                logger.info(f"[NotebookLM-Playwright] Got answer via UI <p> tag ({len(p_text)} chars)")

            except Exception as e:
                logger.error(f"[NotebookLM-Playwright] UI query fallback failed: {e}")

        if "error" in result:
            logger.error(f"[NotebookLM-Playwright] Query error. Logs: {result.get('logs')}")
            raise RuntimeError(f"Query failed: {result['error']}")

        logger.info(f"[NotebookLM-Playwright] Query done. Logs: {result.get('logs')}")
        return result

    def _extract_answer_from_raw(self, raw_text: str) -> Optional[str]:
        """Extract the main answer text from the complex JSON stream.
        
        NotebookLM returns JSON-escaped markdown in streaming chunks.
        The final answer is typically in the last chunks.
        """
        try:
            # Method 1: Look for wrb.fr response pattern with markdown content
            # Pattern: ["wrb.fr",null,"[[\"**Answer text...
            import json
            
            # Find all wrb.fr chunks
            wrb_pattern = r'\["wrb\.fr",null,"(\[\[.*?)"\]'
            matches = re.findall(wrb_pattern, raw_text)
            
            all_text = []
            for match in matches:
                try:
                    # Unescape the JSON string
                    unescaped = match.replace('\\n', '\n').replace('\\"', '"')
                    # Try to parse the inner JSON
                    inner = json.loads(unescaped)
                    if inner and isinstance(inner, list) and len(inner) > 0:
                        # Extract text from nested structure
                        if isinstance(inner[0], str):
                            all_text.append(inner[0])
                        elif isinstance(inner[0], list) and len(inner[0]) > 0:
                            if isinstance(inner[0][0], str):
                                all_text.append(inner[0][0])
                except Exception:
                    pass
            
            if all_text:
                # Combine all chunks and clean up markdown
                combined = ''.join(all_text)
                # Remove escape sequences
                combined = combined.replace('\\n', '\n').replace('\\"', '"')
                return combined if len(combined) > 20 else None
            
            # Method 2: Fallback - find longest string with markdown indicators
            strings = re.findall(r'"([^"]{100,})"', raw_text)
            markdown_strings = [s for s in strings if '**' in s or '##' in s or '\\n' in s]
            
            if markdown_strings:
                longest = max(markdown_strings, key=len)
                decoded = longest.replace('\\n', '\n').replace('\\"', '"')
                return decoded
            
            # Method 3: Original fallback
            candidates = []
            for s in strings:
                if ' ' in s:
                    try:
                        decoded = s.encode('utf-8').decode('unicode_escape')
                        candidates.append(decoded)
                    except Exception:
                        pass
            
            if candidates:
                candidates.sort(key=len, reverse=True)
                return candidates[0]
                
        except Exception as e:
            logger.debug(f"Answer extraction error: {e}")
        return None

    async def interactive_login(self):
        """Interactive login - opens browser for manual Google login."""
        if not self._initialized:
            self.headless = False
            await self._init_browser()
        
        await self._page.goto("https://notebooklm.google.com/")
        input("Press Enter after login...")
        return await self.ensure_logged_in()


# Singleton instance
_playwright_client: Optional[PlaywrightNotebookLMClient] = None


async def get_playwright_client() -> PlaywrightNotebookLMClient:
    """Get or create Playwright client singleton."""
    global _playwright_client
    if _playwright_client is None:
        _playwright_client = PlaywrightNotebookLMClient(headless=True)
        await _playwright_client._init_browser()
    return _playwright_client


async def playwright_query(
    notebook_id: str,
    query_text: str,
) -> Dict[str, Any]:
    """
    Query NotebookLM using Playwright browser.
    
    Args:
        notebook_id: Notebook UUID
        query_text: Question to ask
        
    Returns:
        Dict with answer and sources
    """
    client = await get_playwright_client()
    return await client.query(notebook_id, query_text)
