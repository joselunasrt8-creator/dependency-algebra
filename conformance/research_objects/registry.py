"""Research object projection registry."""

from __future__ import annotations

import importlib
import pkgutil
from pathlib import Path

_HANDLERS = {}
_DISCOVERED = False


def register(research_object_id, handler):
    _HANDLERS[research_object_id] = handler


def discover_handlers():
    """Import projection modules so their register() calls populate the registry."""

    global _DISCOVERED
    if _DISCOVERED:
        return
    package_name = __name__.rsplit(".", 1)[0]
    package_path = Path(__file__).parent
    for module in sorted(pkgutil.iter_modules([str(package_path)]), key=lambda item: item.name):
        if module.name in {"__init__", "registry"}:
            continue
        importlib.import_module(f"{package_name}.{module.name}")
    _DISCOVERED = True


def get_handler(research_object_id):
    discover_handlers()
    return _HANDLERS[research_object_id]
