from config import *
import requests


def get_tokens(login, password):
    data = {
        "email": login,
        "password": password,
    }

    result = requests.post(CTRACK_HOST + 'token/', data=data)

    print(CTRACK_HOST + 'token/', result.text)

    if result.status_code == 200:
        data = result.json()
        return data['access']
    else:
        return None


def get_data(access_token, last_id=0):
    headers = {
        "Authorization": "Bearer " + access_token
    }

    result = requests.get(CTRACK_HOST + 'measurements/', headers=headers)

    print(result.text)

    try:
        data = result.json()
        return list(filter(lambda x: x['id'] > last_id, data['results']))
    except:
        return []

# # Gemocard POST HOST + /subscribe
# {
#     "login": "roctbb",
#     "patient": 0
# }
#
# # Gemocard POST HOST + /unsubscribe
# {
#     "login": "roctbb"
# }
#
# # Medsenger https://medsenger.ru:9105/receive
# {
#     "login": "roctbb",
#     "data": {
#         "systolic": 120,
#         "diastolic": 80,
#         "pulse": 80,
#         # ????
#     }
# }
