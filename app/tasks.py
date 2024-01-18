import json
from asgiref.sync import async_to_sync
from celery import shared_task
from celery.app import default_app
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import datetime
from datetime import time as time_constructor
from django.core.mail import EmailMessage
from django.conf import settings
from django.template.loader import render_to_string
import os


# @shared_task
def send_email_to_user(user_id: int, subject, message):
    User = get_user_model()
    instance = User.objects.get(id=user_id)

    template = os.path.join('emails', 'mail_template.html')
    context = {'user_name': instance.first_name, 'message': message}

    html_content = render_to_string(template, context)
    email_message = EmailMessage(subject, html_content, settings.EMAIL_HOST_USER, [instance.email])
    email_message.content_subtype = 'html'

    try:
        success_count = email_message.send()
        if success_count > 0:
            return f'Email sent successfully to {instance.email}!'
        else:
            return f'Failed to send email to {instance.email}!'
        
    except Exception as e:
        return f'An exception occurred: {e}'