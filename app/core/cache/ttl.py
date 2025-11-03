"""TTL (Time-To-Live) presets for cache entries.

This module defines standard TTL values for different types of cached data.
"""

# TTL presets in seconds
TTL_SHORT = 60  # 1 minute - for semi-dynamic data
TTL_MEDIUM = 300  # 5 minutes - for moderately stable data
TTL_LONG = 1800  # 30 minutes - for stable data
TTL_VERY_LONG = 3600  # 1 hour - for very stable data
TTL_DISABLED = 0  # No caching
