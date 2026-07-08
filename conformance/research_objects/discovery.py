"""Automatic discovery of research object projection modules."""

from __future__ import annotations

import importlib
import pkgutil

import conformance.research_objects as research_objects


def discover() -> None:
    for _, module_name, ispkg in pkgutil.iter_modules(research_objects.__path__):
        if ispkg:
            continue
        if module_name in {"registry", "discovery", "__init__"}:
            continue
        importlib.import_module(
            f"{research_objects.__name__}.{module_name}"
        )
