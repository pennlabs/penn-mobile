from studentlife.settings.base import *  # noqa: F401, F403
from studentlife.settings.base import BACKEND_DOMAIN, PLATFORM_ACCOUNTS


DEBUG = True

PLATFORM_ACCOUNTS.update({"REDIRECT_URI": f"https://{BACKEND_DOMAIN}/accounts/callback/"})
