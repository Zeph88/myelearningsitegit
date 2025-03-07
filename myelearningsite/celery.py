from __future__ import absolute_import

import os
import time

from celery import Celery
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myelearningsite.settings')
app = Celery('myelearningsite', broker='redis://localhost:6379/0',  backend='redis://localhost:6379/0')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
