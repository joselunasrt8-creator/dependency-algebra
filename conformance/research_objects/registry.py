"""Research object projection registry."""

from __future__ import annotations

_HANDLERS = {}


def register(research_object_id, handler):
    _HANDLERS[research_object_id] = handler


def get_handler(research_object_id):
    return _HANDLERS[research_object_id]
