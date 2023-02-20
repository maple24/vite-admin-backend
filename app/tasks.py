# celery task
from celery import shared_task
import time
from django.core.mail import send_mail


# transform this function into a Celery task, decorate it with @shared_task
# is bracet needed
@shared_task
def test_celery():
    for i in range(10):  
        print(i)
    return 'Done'