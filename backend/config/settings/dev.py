from .base import *

DEBUG = True

# In local development, if Redis is not running, locmem cache can act as fallback
try:
    import redis
    r = redis.from_url(REDIS_URL, socket_connect_timeout=1)
    r.ping()
except Exception:
    # Fallback to local memory cache for offline development without Redis service
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "fl-dev-cache",
        }
    }

# Enable Swagger in development
SPECTACULAR_SETTINGS["SERVE_INCLUDE_SCHEMA"] = True

# Permissive CORS in local development for seamless frontend debugging
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True

