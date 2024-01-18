from __future__ import absolute_import, unicode_literals

import os
from pathlib import Path

from celery import Celery

ROOT_DIR = Path(__file__).resolve(strict=True).parent.parent

app = Celery("config")
app.config_from_object("django.conf:settings", namespace="CELERY")

app.autodiscover_tasks()
