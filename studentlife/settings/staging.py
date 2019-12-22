from studentlife.settings.production import *


DEBUG = True

PLATFORM_ACCOUNTS.update(
    {
        'REDIRECT_URI': os.environ.get('LABS_REDIRECT_URI', 'https://{}/accounts/callback/'.format(BACKEND_DOMAIN)),
        'CLIENT_ID': 'clientid',
        'CLIENT_SECRET': 'supersecretclientsecret',
        'PLATFORM_URL': 'https://platform-dev.pennlabs.org',
        'CUSTOM_ADMIN': False,
    }
)
