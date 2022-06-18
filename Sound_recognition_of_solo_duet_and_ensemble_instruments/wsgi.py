"""
WSGI config for Sound_recognition_of_solo_duet_and_ensemble_instruments project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.0/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Sound_recognition_of_solo_duet_and_ensemble_instruments.settings')

application = get_wsgi_application()
