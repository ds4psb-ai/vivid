"""Opal Adapter - Workflow orchestration adapter.

Implements Google Opal-style workflow execution:
- Workflow definition via DAG
- Multi-model orchestration
- Audio overview generation (future)
"""
from __future__ import annotations

import json
import logging
import os
import time
import urllib.request
from typing import Any, Dict, Optional

from app.adapters.base_adapter import AdapterResult, BaseAdapter

logger = logging.getLogger(__name__)

# Environment configuration
ENABLE_EXTERNAL_ADAPTERS = os.getenv("ENABLE_EXTERNAL_ADAPTERS", "false").lower() in ("1", "true", "yes")
OPAL_API_URL = os.getenv("OPAL_API_URL", "")
OPAL_API_KEY = os.getenv("OPAL_API_KEY", "")
EXTERNAL_ADAPTER_TIMEOUT = float(os.getenv("EXTERNAL_ADAPTER_TIMEOUT", "15"))
EXTERNAL_ADAPTER_RETRIES = int(os.getenv("EXTERNAL_ADAPTER_RETRIES", "1"))


class OpalAdapter(BaseAdapter):
    """Opal adapter for workflow orchestration.
    
    When external APIs are enabled, calls the Opal service.
    Otherwise returns simulated results.
    """
    
    def __init__(self):
        super().__init__("opal")
    
    def run(
        self,
        capsule_id: str,
        capsule_version: str,
        inputs: Dict[str, Any],
        params: Dict[str, Any],
        capsule_spec: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> AdapterResult:
        """Run Opal workflow execution."""
        adapter_config = self._extract_adapter_config(capsule_spec)
        pattern_version = self._extract_pattern_version(capsule_spec)
        
        payload = {
            "workflow": adapter_config.get("workflow", "auteur_capsule_v1"),
            "capsule_id": capsule_id,
            "capsule_version": capsule_version,
            "pattern_version": pattern_version,
            "inputs": inputs,
            "params": params,
            "internal_graph_ref": adapter_config.get("internalGraphRef"),
        }
        
        if ENABLE_EXTERNAL_ADAPTERS and OPAL_API_URL:
            try:
                response = self._call_external_api(
                    OPAL_API_URL,
                    OPAL_API_KEY,
                    payload,
                    EXTERNAL_ADAPTER_TIMEOUT,
                    EXTERNAL_ADAPTER_RETRIES,
                )
                
                summary = {
                    "summary": response.get("summary") or response.get("output") or "Opal workflow executed",
                    "workflow": response.get("workflow", "opal"),
                }
                
                # Optional outputs
                if response.get("audio_overview") is not None:
                    summary["audio_overview"] = response["audio_overview"]
                if response.get("mind_map") is not None:
                    summary["mind_map"] = response["mind_map"]
                
                evidence = response.get("evidence_refs", [])
                
                return AdapterResult(
                    summary=summary,
                    evidence_refs=evidence,
                )
                
            except Exception as exc:
                self.logger.warning(f"Opal external call failed: {exc}")
                return AdapterResult(
                    summary={"summary": f"Opal fallback: {exc}"},
                    evidence_refs=[],
                )
        
        # Simulated result when external adapters are disabled
        self.logger.info("Opal adapter disabled or missing URL; returning simulated result")
        return AdapterResult(
            summary={"summary": "Opal simulated workflow result", "workflow": "mock"},
            evidence_refs=[],
        )
    
    def _call_external_api(
        self,
        url: str,
        api_key: str,
        payload: Dict[str, Any],
        timeout: float,
        retries: int,
    ) -> Dict[str, Any]:
        """Call external Opal API with retry logic."""
        body = json.dumps(payload).encode("utf-8")
        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        
        last_exc: Optional[Exception] = None
        for attempt in range(retries + 1):
            try:
                self.logger.info(f"Opal API call {url} attempt={attempt + 1}")
                request = urllib.request.Request(url, data=body, headers=headers, method="POST")
                with urllib.request.urlopen(request, timeout=timeout) as response:
                    data = response.read().decode("utf-8")
                return json.loads(data)
            except Exception as exc:
                last_exc = exc
                self.logger.warning(f"Opal API call failed {url} attempt={attempt + 1} error={exc}")
                if attempt < retries:
                    time.sleep(0.5 * (attempt + 1))
        
        raise last_exc or RuntimeError("Opal API call failed")
