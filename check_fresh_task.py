#!/usr/bin/env python
"""
Check the status of the latest email task
"""
import os
import sys
import django
import time

# Setup Django environment
sys.path.append('/home/ulrich/ALX_PRODEV/alx-project-nexus')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'e_commerce_api.settings')

django.setup()

from celery.result import AsyncResult
from accounts.tasks import send_verification_email_task

def check_latest_task():
    print("Testing task queuing and checking status...")
    
    # Queue a new task
    result = send_verification_email_task.delay("ulricharmely@gmail.com", "987654")
    task_id = result.id
    print(f"New task queued with ID: {task_id}")
    
    # Wait a bit for the task to be processed
    print("Waiting for task to be processed...")
    for i in range(10):  # Check 10 times
        time.sleep(2)  # Wait 2 seconds between checks
        task_result = AsyncResult(task_id)
        print(f"Attempt {i+1}: Status = {task_result.status}")
        
        if task_result.ready():
            if task_result.successful():
                print(f"✅ Task completed successfully!")
                print(f"Result: {task_result.result}")
                return
            else:
                print(f"❌ Task failed!")
                print(f"Error: {task_result.info}")
                return
        elif task_result.failed():
            print(f"❌ Task failed!")
            print(f"Error: {task_result.info}")
            return
    
    print("⚠️  Task is still processing or may have hung. Check Celery worker logs.")

if __name__ == "__main__":
    check_latest_task()