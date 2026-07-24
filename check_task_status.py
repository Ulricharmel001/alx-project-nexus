#!/usr/bin/env python
"""
Check the status of recently queued email tasks
"""
import os
import sys
import django
from celery.result import AsyncResult

# Setup Django environment
sys.path.append('/home/ulrich/ALX_PRODEV/alx-project-nexus')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'e_commerce_api.settings')

django.setup()

from accounts.tasks import send_verification_email_task, send_welcome_email_task
from django.conf import settings

def check_task_status():
    print("Checking status of email tasks...")
    
    # Use the configured email for testing
    test_email = settings.EMAIL_HOST_USER
    test_code = "CHK99"
    test_name = "Status Check"
    
    # Queue a new task to test
    result = send_verification_email_task.delay(test_email, test_code)
    task_id = result.id
    
    print(f"New task queued with ID: {task_id}")
    
    # Check the status multiple times
    for i in range(10):  # Check 10 times
        res = AsyncResult(task_id)
        print(f"Attempt {i+1}: Status = {res.status}")
        
        if res.ready():
            print(f"Result: {res.result}")
            if res.successful():
                print("✅ Task completed successfully!")
            elif res.failed():
                print(f"❌ Task failed: {res.traceback}")
            break
        else:
            import time
            time.sleep(2)  # Wait 2 seconds before next check
    
    if not res.ready():
        print("⚠️  Task is still processing or may have hung. Check Celery worker logs.")

if __name__ == "__main__":
    check_task_status()