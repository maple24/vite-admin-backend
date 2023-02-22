# celery task
from celery import shared_task
import requests
from loguru import logger


ROUTE = {
    'execute_task': 'http://localhost:8000/api/v1/agent/task/{0}/execute_task/'
}

# transform this function into a Celery task, decorate it with @shared_task
# is bracet needed
'''
# test from django shell
from app.tasks import test_celery 
from datetime import datetime
from datetime import datetime, timedelta
task = test_celery.apply_async(eta=datetime.utcnow()+timedelta(seconds=10))
task.revoke()
'''
@shared_task
def test_celery():
    for i in range(10):  
        print(i)
    return 'Done'

@shared_task
def execute_task(id: int):
    url = ROUTE.get('execute_task').format(id)
    try:
        response = requests.post(url)
        if response.status_code == 201:
            logger.success("Trigger task successfully!")
        else:
            logger.warning(f"Fail to run task, status code: {response.status_code}")
    except Exception as e:
        logger.exception(e)


if __name__ == '__main__':
    execute_task(18)
    
        