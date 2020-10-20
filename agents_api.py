from config import *
import requests


def send_message(contract_id, text, action_link=None, action_name=None, action_onetime=True, only_doctor=False,
                 only_patient=False, action_deadline=None, is_urgent=False, need_answer=False,
                 attachments=None):
    message = {
        "text": text
    }

    if action_link:
        message['action_link'] = action_link

    if action_name:
        message['action_name'] = action_name

    if action_onetime:
        message['action_onetime'] = action_onetime

    if only_doctor:
        message['only_doctor'] = only_doctor

    if need_answer:
        message['need_answer'] = need_answer

    if only_patient:
        message['only_patient'] = only_patient

    if action_deadline:
        message['action_deadline'] = action_deadline

    if is_urgent:
        message['is_urgent'] = is_urgent

    if attachments:
        message['attachments'] = []

        for attachment in attachments:
            message['attachments'].append({
                "name": attachment[0],
                "type": attachment[1],
                "base64": attachment[2],
            })

    data = {
        "contract_id": contract_id,
        "api_key": APP_KEY,
        "message": message
    }

    try:
        requests.post(MAIN_HOST + '/api/agents/message', json=data)
    except Exception as e:
        print('connection error', e)


def get_categories():
    data = {
        "api_key": APP_KEY,
    }

    try:
        result = requests.post(MAIN_HOST + '/api/agents/records/categories', json=data)
        return result.json()
    except Exception as e:
        print('connection error', e)
        return {}


def get_available_categories(contract_id):
    data = {
        "contract_id": contract_id,
        "api_key": APP_KEY,
    }

    try:
        result = requests.post(MAIN_HOST + '/api/agents/records/available_categories', json=data)
        return result.json()
    except Exception as e:
        print('connection error', e)
        return {}


def get_records(contract_id, category_name, time_from=None, time_to=None, limit=None, offset=None):
    data = {
        "contract_id": contract_id,
        "api_key": APP_KEY,
        "category_name": category_name,
    }

    if limit:
        data['limit'] = limit
    if offset:
        data['offset'] = offset
    if time_from:
        data['from'] = time_from
    if time_to:
        data['to'] = time_to

    try:
        result = requests.post(MAIN_HOST + '/api/agents/records/get', json=data)
        return result.json()
    except Exception as e:
        print('connection error', e)
        return {}


def add_record(contract_id, category_name, value, record_time=None):
    data = {
        "contract_id": contract_id,
        "api_key": APP_KEY,
        "category_name": category_name,
        "value": value,
    }

    if record_time:
        data['time'] = record_time

    try:
        answer = requests.post(MAIN_HOST + '/api/agents/records/add', json=data)
    except Exception as e:
        print('connection error', e)


def add_records(contract_id, values, record_time=None):
    data = {
        "contract_id": contract_id,
        "api_key": APP_KEY,
    }

    if record_time:
        data['values'] = [{"category_name": category_name, "value": value, "time": record_time} for
                          (category_name, value) in values]
    else:
        data['values'] = [{"category_name": category_name, "value": value} for (category_name, value) in values]
    try:
        requests.post(MAIN_HOST + '/api/agents/records/add', json=data)
    except Exception as e:
        print('connection error', e)
