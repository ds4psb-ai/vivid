"""
Playwright-based NotebookLM Query Client

Uses real browser context to execute RPC queries, bypassing TLS fingerprint checks.
Google binds cookies to browser fingerprint, so Python HTTP clients fail with 401.
This module uses Playwright to run queries in a real Chromium browser context.

Usage:
    from app.rag.notebooklm_playwright import PlaywrightNotebookLMClient
    
    async with PlaywrightNotebookLMClient() as client:
        result = await client.query("ae5eb68f-...", "기생충에서 계단의 의미는?")
        print(result["answer"])
"""

import asyncio
import json
import logging
import os
import re
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# User data directory for persistent browser session
BROWSER_DATA_DIR = Path.home() / ".notebooklm-mcp" / "playwright-profile"


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
    
    async def _init_browser(self):
        """Initialize Playwright browser - CDP or persistent context."""
        if self._initialized:
            return
        
        try:
            from playwright.async_api import async_playwright
            
            self._playwright = await async_playwright().start()
            
            if self._use_cdp:
                # CDP mode: Connect to existing Chrome with remote debugging
                logger.info(f"[NotebookLM-Playwright] Connecting to Chrome CDP port {self.cdp_port}")
                self._browser = await self._playwright.chromium.connect_over_cdp(
                    f"http://localhost:{self.cdp_port}"
                )
                
                # Get existing contexts/pages
                contexts = self._browser.contexts
                if contexts:
                    self._context = contexts[0]
                    # Find NotebookLM page or use first page
                    for page in self._context.pages:
                        if "notebooklm.google.com" in page.url:
                            self._page = page
                            break
                    if not self._page and self._context.pages:
                        self._page = self._context.pages[0]
                
                if not self._page:
                    self._page = await self._context.new_page()
                    
                logger.info(f"[NotebookLM-Playwright] Connected via CDP, page: {self._page.url}")
                
                # Inject cookies from cached auth.json (Try auto-login)
                await self._inject_cached_cookies()
            else:
                # Standalone mode: Launch new browser with persistent profile
                BROWSER_DATA_DIR.mkdir(parents=True, exist_ok=True)
                
                self._context = await self._playwright.chromium.launch_persistent_context(
                    user_data_dir=str(BROWSER_DATA_DIR),
                    headless=self.headless,
                    args=[
                        "--disable-blink-features=AutomationControlled",
                        "--no-sandbox",
                    ],
                    viewport={"width": 1280, "height": 800},
                    locale="ko-KR",
                )
                
                # Get or create page
                if self._context.pages:
                    self._page = self._context.pages[0]
                else:
                    self._page = await self._context.new_page()
                
                # Inject cookies from cached auth.json if available
                await self._inject_cached_cookies()
            
            self._initialized = True
            logger.info("[NotebookLM-Playwright] Browser initialized")
            
        except Exception as e:
            logger.error(f"[NotebookLM-Playwright] Failed to init browser: {e}")
            raise
    
    async def close(self):
        """Close browser and cleanup."""
        if self._context:
            await self._context.close()
        if self._playwright:
            await self._playwright.stop()
        self._initialized = False
        logger.info("[NotebookLM-Playwright] Browser closed")
    
    async def _inject_cached_cookies(self):
        """Inject cookies from cached auth.json into browser context."""
        auth_file = Path.home() / ".notebooklm-mcp" / "auth.json"
        
        if not auth_file.exists():
            logger.debug("[NotebookLM-Playwright] No cached auth.json found")
            return
        
        try:
            with open(auth_file) as f:
                auth_data = json.load(f)
            
            cookies = auth_data.get("cookies", {})
            if not cookies:
                return
            
            # Convert to Playwright cookie format
            playwright_cookies = []
            for name, value in cookies.items():
                playwright_cookies.append({
                    "name": name,
                    "value": value,
                    "domain": ".google.com",
                    "path": "/",
                    "httpOnly": name.startswith("__Secure") or name in ("SID", "HSID", "SSID"),
                    "secure": name.startswith("__Secure") or name in ("SID", "HSID", "SSID", "SIDCC"),
                })
            
            # Add cookies to context
            await self._context.add_cookies(playwright_cookies)
            logger.info(f"[NotebookLM-Playwright] Injected {len(playwright_cookies)} cookies from cache")
            
        except Exception as e:
            logger.warning(f"[NotebookLM-Playwright] Failed to inject cookies: {e}")
    
    async def ensure_logged_in(self) -> bool:
        """
        Check if logged into NotebookLM and navigate to it.
        
        Returns:
            True if logged in, False if login required
        """
        if "notebooklm.google.com" not in self._page.url:
             await self._page.goto("https://notebooklm.google.com/", wait_until="domcontentloaded")
             await asyncio.sleep(2) # Wait for redirects
        
        # Check if redirected to login
        current_url = self._page.url
        if "accounts.google.com" in current_url or "signin" in current_url:
            logger.warning("[NotebookLM-Playwright] Login required (redirected to accounts)")
            return False
        
        # Check for notebook list or welcome page
        try:
            # Try to wait for common elements, but don't fail if not found immediately
            # Just relying on URL being notebooklm.google.com is strong enough indicator usually
            try:
                await self._page.wait_for_selector("text=Recent Notebooks", timeout=3000)
            except Exception:
                pass  # Selector not found, that's OK
                
            if "notebooklm.google.com" in current_url:
                logger.info("[NotebookLM-Playwright] Logged in successfully (URL check)")
                return True
                
            logger.warning("[NotebookLM-Playwright] Not on NotebookLM URL")
            return False
        except Exception as e:
            # Fallback
            return "notebooklm.google.com" in current_url

    async def query(
        self,
        notebook_id: str,
        query_text: str,
        timeout_ms: int = 60000,
    ) -> Dict[str, Any]:
        """
        Execute a query against a NotebookLM notebook.
        
        Args:
            notebook_id: The notebook UUID
            query_text: The question to ask
            timeout_ms: Query timeout in milliseconds (increased for research/streaming)
            
        Returns:
            Dict with answer, sources, and metadata
        """
        if not self._initialized:
            await self._init_browser()
        
        # Navigate to notebook if needed
        notebook_url = f"https://notebooklm.google.com/notebook/{notebook_id}"
        # Only navigate if strict match fails (ignoring params)
        if notebook_id not in self._page.url:
            await self._page.goto(notebook_url, wait_until="domcontentloaded")
            await asyncio.sleep(2)
        
        # Check login status
        if "accounts.google.com" in self._page.url:
            raise RuntimeError("Login required. Run interactive login first.")
        
        # Execute RPC query via JavaScript in browser context
        # Use format() instead of f-string to avoid escaping issues with JS code
        js_code = """
            async () => {
                const logs = [];
                function log(msg) { logs.push(msg); }
                
                try {
                    log("Starting query...");
                    
                    // Extract tokens & BL version
                    const pageSource = document.documentElement.outerHTML;
                    const csrfMatch = pageSource.match(/"SNlM0e":"([^"]+)"/);
                    const csrf = csrfMatch ? csrfMatch[1] : null;
                    const sidMatch = pageSource.match(/"FdrFJe":"([^"]+)"/);
                    const sid = sidMatch ? sidMatch[1] : null;
                    
                    // Get dynamic backend version (bl)
                    const bl = (window.WIZ_global_data && window.WIZ_global_data.cfb2h) 
                        ? window.WIZ_global_data.cfb2h 
                        : "boq_labs-tailwind-frontend_20251221.14_p0"; // Fallback
                    
                    log("BL Version: " + bl);

                    if (!csrf) {
                        return { error: "CSRF token not found", logs: logs };
                    }

                    const notebookId = "NOTEBOOK_ID_PLACEHOLDER";
                    const query = QUERY_PLACEHOLDER;
                    const reqIdBase = Math.floor(Math.random() * 900000) + 100000;

                    // 1. Fetch Source IDs using rLM1Ne (GetNotebook)
                    let sourceIds = [];
                    try {
                        log("Fetching Source IDs via rLM1Ne...");
                        const getNotebookParams = [notebookId, null, [2], null, 0];
                        const rpcEnvelope = [[["rLM1Ne", JSON.stringify(getNotebookParams), null, "generic"]]];
                        
                        const rpcBody = new URLSearchParams();
                        rpcBody.append("f.req", JSON.stringify(rpcEnvelope));
                        rpcBody.append("at", csrf);
                        
                        const rpcUrl = `https://notebooklm.google.com/_/LabsTailwindUi/data/batchexecute?rpcids=rLM1Ne&source-path=/notebook/${notebookId}&f.sid=${sid}&bl=${bl}&hl=en&_reqid=${reqIdBase}&rt=c`;
                        
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
                                const parsed = JSON.parse(line);
                                if (parsed[0] && parsed[0][1] === "rLM1Ne") {
                                    log("Found rLM1Ne response chunk");
                                    const data1 = JSON.parse(parsed[0][2]);
                                    
                                    // Robust Regex Extraction for UUIDs
                                    // Structure parsing is fragile, so we find all UUIDs in the JSON string
                                    // and assume they are source IDs (except the notebook ID itself)
                                    const dataStr = JSON.stringify(data1);
                                    // Regex for UUIDs
                                    const uuidPattern = /[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}/gi;
                                    const matches = dataStr.match(uuidPattern);
                                    
                                    if (matches) {
                                        const found = new Set(matches);
                                        found.delete(notebookId); // Remove notebook ID
                                        sourceIds = Array.from(found);
                                    }
                                }
                            }
                        }
                    } catch (e) {
                         log(`RPC Error: ${e.message}`);
                    }
                    
                    log(`Extracted Source IDs: ${sourceIds.length} found`);

                    // 2. Execute Query using GenerateFreeFormStreamed
                    const conversationId = crypto.randomUUID();

                    // Sources structure: [[[sid]]] for each
                    const sourcesArray = sourceIds.map(sid => [[[sid]]]);

                    const params = [
                        sourcesArray,
                        query,
                        null,  // conversation history (null for new)
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
                        headers: {"Content-Type": "application/x-www-form-urlencoded;charset=UTF-8"},
                        body: formData.toString(),
                        credentials: "include"
                    });
                    
                    const text = await response.text();
                    log(`Stream Response Length: ${text.length}`);

                    return {
                        status: response.status,
                        success: response.ok,
                        source_count: sourceIds.length,
                        raw_response: text.substring(0, 50000), // Larger buffer
                        notebook_id: notebookId,
                        logs: logs
                    };
                } catch (e) {
                    return { error: e.message, logs: logs };
                }
            }
        """

        # Replace placeholders
        js_code = js_code.replace("NOTEBOOK_ID_PLACEHOLDER", notebook_id)
        js_code = js_code.replace("QUERY_PLACEHOLDER", json.dumps(query_text))

        result = await self._page.evaluate(js_code)
        
        # Post-Processing: Extract answer
        if result.get("success") and result.get("raw_response"):
            raw = result["raw_response"]
            if raw.startswith(")]}'"):
                raw = raw[4:].strip()
            
            result["answer"] = self._extract_answer_from_raw(raw) or "No answer found (extraction failed)."

        if "error" in result:
            logger.error(f"[NotebookLM-Playwright] Query error. Logs: {result.get('logs')}")
            raise RuntimeError(f"Query failed: {result['error']}")

        logger.info(f"[NotebookLM-Playwright] Query done. Logs: {result.get('logs')}")
        return result

    def _extract_answer_from_raw(self, raw_text: str) -> Optional[str]:
        """Attempt to extract the main answer text from the complex JSON stream."""
        try:
            # Find all string literals > 50 chars
            strings = re.findall(r'"([^"]{50,})"', raw_text)
            if not strings:
                return None
            
            candidates = []
            for s in strings:
                if ' ' in s: 
                    try:
                        decoded = s.encode('utf-8').decode('unicode_escape')
                        candidates.append(decoded)
                    except Exception:
                        pass  # Unicode decode error, skip
            
            if candidates:
                # Prioritize strings with Korean chars if possible, but length is good heuristic
                candidates.sort(key=len, reverse=True)
                return candidates[0]
                
        except Exception:
            pass
        return None

    async def interactive_login(self):
        """Interactive login - (Same as before)"""
        if not self._initialized:
            self.headless = False
            await self._init_browser()
        
        await self._page.goto("https://notebooklm.google.com/")
        input("Press Enter after login...")
        if await self.ensure_logged_in():
            print("Login success")
            return True
        return False


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
