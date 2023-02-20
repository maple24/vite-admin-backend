'''
motivation: long-running processes should be run outside the normal HTTP request/response flow, in a background process
Producer: Your Django app
Message Broker: The Redis server
Consumer: Your Celery app

# for windows, celery worker has to run with command below
celery -A your-application worker -l info --pool=solo
# or
pip install gevent
celery -A <module> worker -l info -P gevent

# celery beat
celery -A <module> beat -l nfo
'''
import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backendviteadmin.settings")
app = Celery("backendviteadmin")
# define the Django settings file as the configuration file for Celery
# namespace is binded with celery setting name in settings.py
app.config_from_object("django.conf:settings", namespace="CELERY")
# tell your Celery application instance to automatically find all tasks in each app of your Django project
app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    print('Request: {0!r}'.format(self.request))