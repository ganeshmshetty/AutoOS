"""
shared_state.py — Global context buffer for Cross-Domain Data Chaining.
Allows Browser Agent and OS Modules to pass data between each other.
"""
from typing import Any
import logging

logger = logging.getLogger("AutoOS.shared_state")

class SharedStateManager:
    _data_buffer = {
        "last_extracted_text": None,
        "last_url": None,
        "last_app": None,
        "last_entities": []
    }

    @classmethod
    def set(cls, key: str, value: Any):
        logger.debug("Setting shared state: %s = %r", key, value)
        cls._data_buffer[key] = value

    @classmethod
    def get(cls, key: str, default=None):
        return cls._data_buffer.get(key, default)

    @classmethod
    def get_all(cls):
        return cls._data_buffer.copy()

    @classmethod
    def clear(cls):
        cls._data_buffer = {k: None for k in cls._data_buffer}
        cls._data_buffer["last_entities"] = []
