"""
ASGI config for Sound_recognition_of_solo_duet_and_ensemble_instruments project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.0/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Sound_recognition_of_solo_duet_and_ensemble_instruments.settings')

application = get_asgi_application()
