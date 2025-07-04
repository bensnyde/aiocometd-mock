import pkgutil
import importlib
from typing import List, Callable, Dict, Any

from aiohttp import web

adapters: List[Callable] = []


def register_adapter(func: Callable):
    """Register a message adapter."""
    adapters.append(func)
    return func


def load_adapters(adapter_names: List[str] | None = None):
    """Load adapters from the 'adapters' package."""
    # Clear existing adapters to avoid duplicates during reloads
    adapters.clear()

    for name in adapter_names:
        try:
            importlib.import_module(f".{name}", __package__)
        except ImportError:
            # Handle the case where a specified adapter doesn't exist
            print(f"Warning: Adapter '{name}' not found.")


async def run_adapters(request: web.Request, payload: List[Dict[str, Any]]):
    """Run all registered adapters."""
    for adapter in adapters:
        response = await adapter(request, payload)
        if response:
            return response
    return None