from flask import current_app
from cachetools import TTLCache


class VerifyHashCache:
    """Cache handler to make it quick password check by bypassing
    already checked passwords against exact same couple of token/password.
    This cache handler is more efficient on small apps that
    run on few processes as cache is only shared between threads."""

    def __init__(self):
        ttl = current_app.config.get("VERIFY_HASH_CACHE_TTL", 60 * 5)
        max_size = current_app.config.get("VERIFY_HASH_CACHE_MAX_SIZE", 500)
        self._cache = TTLCache(max_size, ttl)

    def has_verify_hash_cache(self, user):
        """Check given user id is in cache."""
        return self._cache.get(user.id)

    def set_cache(self, user):
        """When a password is checked, then result is put in cache."""
        self._cache[user.id] = True

    def clear(self):
        """Clear cache"""
        self._cache.clear()
