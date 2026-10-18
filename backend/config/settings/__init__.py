import os

# Default to dev settings if not explicitly specified
env = os.getenv("DJANGO_SETTINGS_MODULE", "config.settings.dev")

if env == "config.settings.prod":
    from .prod import *
elif env == "config.settings.test":
    from .test import *
else:
    from .dev import *
