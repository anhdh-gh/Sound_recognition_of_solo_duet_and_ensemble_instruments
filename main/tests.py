import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Sound_recognition_of_solo_duet_and_ensemble_instruments.settings")
django.setup()

from main.models import File


File.objects.all().delete()