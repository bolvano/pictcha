from django.db import models
from django.utils import timezone

from django.db.models.signals import pre_delete
from django.contrib.sessions.models import Session

from django.conf import settings

import shutil
import os

def sessionend_handler(sender, **kwargs):
    '''
    deletes session folder for expired session
    needs cron to be set to
    "python manage.py clearsessions" every once in a while
    '''
    session_key = kwargs.get('instance').session_key
    print("session %s ended" % session_key)
    session_dir = os.path.join(settings.MEDIA_ROOT, session_key)
    try:
        shutil.rmtree(session_dir)
    except Exception:
        pass

pre_delete.connect(sessionend_handler, sender=Session) # putting the trigger

