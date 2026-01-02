#!/usr/bin/env python3
"""Sandbox Runner.

Secure execution wrapper that:
1. Reads input from stdin or file
2. Validates and sanitizes code
3. Executes in restricted environment
4. Returns JSON output to stdout
"""
import ast
import builtins
import importlib
import io
import json
import re
import sys
import traceback
from contextlib import redirect_stdout, redirect_stderr
from typing import Any, Dict, Optional, Set

# Max output size (1MB)
MAX_OUTPUT_SIZE = 1024 * 1024

# Execution timeout handled by Docker, but also limit here
INTERNAL_TIMEOUT = 25  # seconds


# =============================================================================
# Code Validator
# =============================================================================

class CodeValidator:
    """Validates Python code for safety."""
    
    # Dangerous modules that should NEVER be imported
    BANNED_MODULES: Set[str] = {
        'os', 'sys', 'subprocess', 'shutil', 'pathlib',
        'socket', 'asyncio', 'multiprocessing', 'threading',
        'ctypes', 'pickle', 'marshal', 'shelve',
        'tempfile', 'glob', 'fnmatch',
        'importlib', 'pkgutil', 'zipimport',
        'code', 'codeop', 'compile',
        'pty', 'tty', 'termios',
        'resource', 'grp', 'pwd',
        '__builtin__', 'builtins',
    }
    
    # Dangerous functions / attributes
    BANNED_PATTERNS: Set[str] = {
        r'__import__',
        r'eval\s*\(',
        r'exec\s*\(',
        r'compile\s*\(',
        r'open\s*\(',
        r'file\s*\(',
        r'input\s*\(',
        r'raw_input\s*\(',
        r'globals\s*\(',
        r'locals\s*\(',
        r'vars\s*\(',
        r'dir\s*\(',
        r'getattr\s*\(',
        r'setattr\s*\(',
        r'delattr\s*\(',
        r'hasattr\s*\(',
        r'__.*__',  # dunder methods
    }
    
    @classmethod
    def validate(cls, code: str) -> tuple[bool, Optional[str]]:
        """
        Validate code for safety.
        
        Returns:
            (is_safe, error_message)
        """
        # Check for banned patterns
        for pattern in cls.BANNED_PATTERNS:
            if re.search(pattern, code, re.IGNORECASE):
                return False, f"Forbidden pattern detected: {pattern}"
        
        # Parse AST
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            return False, f"Syntax error: {e}"
        
        # Check imports
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.split('.')[0] in cls.BANNED_MODULES:
                        return False, f"Banned import: {alias.name}"
            
            elif isinstance(node, ast.ImportFrom):
                if node.module and node.module.split('.')[0] in cls.BANNED_MODULES:
                    return False, f"Banned import from: {node.module}"
            
            # Check for dangerous function calls
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    if node.func.id in {'eval', 'exec', 'compile', 'open', '__import__'}:
                        return False, f"Forbidden function: {node.func.id}"
        
        return True, None


# =============================================================================
# Safe Builtins
# =============================================================================

def get_safe_builtins() -> Dict[str, Any]:
    """Get restricted builtins."""
    safe = {}
    
    # Allowed builtins
    allowed = {
        # Types
        'bool', 'int', 'float', 'str', 'bytes', 'bytearray',
        'list', 'tuple', 'set', 'frozenset', 'dict',
        'type', 'object',
        
        # Functions
        'len', 'range', 'enumerate', 'zip', 'map', 'filter',
        'sorted', 'reversed', 'min', 'max', 'sum', 'any', 'all',
        'abs', 'round', 'pow', 'divmod',
        'isinstance', 'issubclass',
        'iter', 'next',
        'format', 'repr', 'ascii', 'chr', 'ord',
        'bin', 'hex', 'oct',
        'hash', 'id',
        'slice',
        
        # Exceptions (for try/except)
        'Exception', 'BaseException', 'StopIteration',
        'TypeError', 'ValueError', 'KeyError', 'IndexError',
        'AttributeError', 'RuntimeError', 'NotImplementedError',
        
        # Constants
        'True', 'False', 'None',
        
        # Print for debugging
        'print',
    }
    
    for name in allowed:
        if hasattr(builtins, name):
            safe[name] = getattr(builtins, name)
    
    return safe


# =============================================================================
# Safe Modules
# =============================================================================

def get_safe_modules() -> Dict[str, Any]:
    """Get safe modules for sandboxed code."""
    modules = {}
    
    # JSON is always safe
    modules['json'] = importlib.import_module('json')
    
    # Math is safe
    modules['math'] = importlib.import_module('math')
    
    # re is mostly safe for text processing
    modules['re'] = importlib.import_module('re')
    
    # datetime is safe
    modules['datetime'] = importlib.import_module('datetime')
    
    # collections is safe
    modules['collections'] = importlib.import_module('collections')
    
    # itertools is safe
    modules['itertools'] = importlib.import_module('itertools')
    
    # functools is safe
    modules['functools'] = importlib.import_module('functools')
    
    # string is safe
    modules['string'] = importlib.import_module('string')
    
    # httpx for API calls (when network allowed)
    try:
        modules['httpx'] = importlib.import_module('httpx')
    except ImportError:
        pass
    
    # jinja2 for templates
    try:
        modules['jinja2'] = importlib.import_module('jinja2')
    except ImportError:
        pass
    
    return modules


# =============================================================================
# Executor
# =============================================================================

def execute_code(code: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute code in sandboxed environment.
    
    Args:
        code: Python code to execute
        input_data: Input parameters
        
    Returns:
        Execution result dict
    """
    # Validate code
    is_safe, error = CodeValidator.validate(code)
    if not is_safe:
        return {
            'success': False,
            'error': error,
            'error_code': 'VALIDATION_FAILED',
        }
    
    # Prepare restricted globals
    safe_globals = {
        '__builtins__': get_safe_builtins(),
        '__name__': '__main__',
        'input_data': input_data,
    }
    
    # Add safe modules
    safe_globals.update(get_safe_modules())
    
    # Capture output
    stdout_capture = io.StringIO()
    stderr_capture = io.StringIO()
    
    try:
        # Execute with captured output
        with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
            # Execute the code
            exec(code, safe_globals)
            
            # Look for result
            result = None
            
            # Check for result variable
            if 'result' in safe_globals:
                result = safe_globals['result']
            elif 'output' in safe_globals:
                result = safe_globals['output']
            elif 'process' in safe_globals and callable(safe_globals['process']):
                result = safe_globals['process'](input_data)
            elif 'main' in safe_globals and callable(safe_globals['main']):
                result = safe_globals['main'](input_data)
        
        return {
            'success': True,
            'output': result,
            'stdout': stdout_capture.getvalue()[:MAX_OUTPUT_SIZE],
            'stderr': stderr_capture.getvalue()[:MAX_OUTPUT_SIZE],
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'error_code': type(e).__name__,
            'traceback': traceback.format_exc()[:5000],
            'stdout': stdout_capture.getvalue()[:MAX_OUTPUT_SIZE],
            'stderr': stderr_capture.getvalue()[:MAX_OUTPUT_SIZE],
        }


# =============================================================================
# Main
# =============================================================================

def main():
    """Main entry point."""
    try:
        # Read input from stdin
        input_json = sys.stdin.read()
        if not input_json:
            # Try reading from file
            try:
                with open('/sandbox/input.json', 'r') as f:
                    input_json = f.read()
            except FileNotFoundError:
                input_json = '{}'
        
        # Parse input
        try:
            payload = json.loads(input_json)
        except json.JSONDecodeError as e:
            print(json.dumps({
                'success': False,
                'error': f'Invalid JSON input: {e}',
                'error_code': 'JSON_DECODE_ERROR',
            }))
            sys.exit(1)
        
        code = payload.get('code', '')
        input_data = payload.get('input_data', {})
        
        if not code:
            print(json.dumps({
                'success': False,
                'error': 'No code provided',
                'error_code': 'NO_CODE',
            }))
            sys.exit(1)
        
        # Execute
        result = execute_code(code, input_data)
        
        # Output
        print(json.dumps(result, default=str))
        
    except Exception as e:
        print(json.dumps({
            'success': False,
            'error': str(e),
            'error_code': 'RUNNER_ERROR',
            'traceback': traceback.format_exc()[:5000],
        }))
        sys.exit(1)


if __name__ == '__main__':
    main()
