import logging
import os
import time

import openai
import requests

logger = logging.getLogger("openai_splunk_monitor")


def send_to_splunk(response, request, duration):
    splunk_hec_url = os.environ.get('SPLUNK_HEC_URL')
    splunk_token = os.environ.get('SPLUNK_HEC_TOKEN')

    headers = {'Authorization': f'Splunk {splunk_token}'}
    data = {
        'event': {
            'request': request,
            'response': response,
            'response_time': duration
        }
    }

    r = requests.post(splunk_hec_url, headers=headers, json=data)
    logger.debug(f"Send event to Splunk HEC:\n{data}")

    if r.status_code != 200:
        logger.error(f'Error sending data to Splunk HEC: {r.status_code} {r.text}')


def time_function(func, *args, **kwargs):
    logger.debug(f"Running the original function: '{func.__qualname__}'. args:{args}; kwargs: {kwargs}")

    start_time = time.time()
    response = func(*args, **kwargs)
    end_time = time.time()
    duration = round(end_time - start_time, 3)

    return response, duration


def init_monitor():
    original_completion_create = openai.Completion.create
    original_chat_completion_create = openai.ChatCompletion.create

    def new_completion_create(*args, **kwargs):
        response, duration = time_function(original_completion_create, *args, **kwargs)
        send_to_splunk(response, kwargs, duration)
        return response

    def new_chat_completion_create(*args, **kwargs):
        response, duration = time_function(original_chat_completion_create, *args, **kwargs)
        send_to_splunk(response, kwargs, duration)
        return response

    openai.Completion.create = new_completion_create
    openai.ChatCompletion.create = new_chat_completion_create
