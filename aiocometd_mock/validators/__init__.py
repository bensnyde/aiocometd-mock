import pkgutil
import importlib
from typing import List, Callable, Dict, Any

from aiohttp import web

validators: List[Callable] = []


def register_validator(func: Callable):
    """Register a message validator."""
    validators.append(func)
    return func


def load_validators(validator_names: List[str] | None = None):
    """Load validators from the 'validators' package."""
    # Clear existing validators to avoid duplicates during reloads
    validators.clear()

    if validator_names:
        for name in validator_names:
            try:
                importlib.import_module(f".{name}", __package__)
            except ImportError:
                # Handle the case where a specified validator doesn't exist
                print(f"Warning: Validator '{name}' not found.")


async def run_validators(request: web.Request, payload: List[Dict[str, Any]]):
    """Run all registered validators."""
    if request.app.get("no_validation"):
        return None
    for validator_func in validators:
        response = await validator_func(request, payload)
        if response:
            return response
    return None