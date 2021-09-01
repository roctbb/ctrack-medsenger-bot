from threading import Thread

from flask import Flask, request, render_template
import json
import time
import datetime
from config import *
import ctrack_api
from medsenger_api import AgentApiClient
from flask_sqlalchemy import SQLAlchemy

from helpers import verify_json, verify_get

app = Flask(__name__)
db_string = "postgres://{}:{}@{}:{}/{}".format(DB_LOGIN, DB_PASSWORD, DB_HOST, DB_PORT, DB_DATABASE)
app.config['SQLALCHEMY_DATABASE_URI'] = db_string
db = SQLAlchemy(app)
medsenger_api = AgentApiClient(API_KEY, MAIN_HOST, AGENT_ID, API_DEBUG)


def gts():
    now = datetime.datetime.now()
    return now.strftime("%Y-%m-%d %H:%M:%S")


class Contract(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    active = db.Column(db.Boolean, default=True)
    error_sent = db.Column(db.Boolean, default=False)
    login = db.Column(db.String(255), default='')
    password = db.Column(db.String(255), default='')
    access_token = db.Column(db.String(255), default='')
    last_id = db.Column(db.Integer(), default=0)
    last_access_request = db.Column(db.Integer(), default=0)


try:
    db.create_all()
except:
    print('cant create structure')


@app.route('/status', methods=['POST'])
@verify_json
def status():
    contract_ids = [contract.id for contract in Contract.query.filter_by(active=True).all()]

    answer = {
        "is_tracking_data": True,
        "supported_scenarios": [],
        "tracked_contracts": contract_ids
    }

    return json.dumps(answer)


@app.route('/init', methods=['POST'])
@verify_json
def init():
    data = request.json
    contract_id = int(data['contract_id'])
    query = Contract.query.filter_by(id=contract_id)
    if query.count() != 0:
        contract = query.first()
        contract.active = True

        print("{}: Reactivate contract {}".format(gts(), contract.id))
    else:
        contract = Contract(id=contract_id)
        db.session.add(contract)

        print("{}: Add contract {}".format(gts(), contract.id))

    if 'params' in data:
        login = data.get('params', {}).get('ctrack_login', '')
        password = data.get('params', {}).get('ctrack_password', '')

        if login and password:
            access = ctrack_api.get_tokens(login, password)
            if access:
                contract.access_token = access
                contract.login = login
                contract.password = password
                contract.last_access_request = time.time()

    db.session.commit()

    if not contract.access_token:
        send_auth_request(contract.id)

    return 'ok'


@app.route('/remove', methods=['POST'])
@verify_json
def remove():
    data = request.json

    contract_id = str(data['contract_id'])
    query = Contract.query.filter_by(id=contract_id)

    if query.count() != 0:
        contract = query.first()
        contract.active = False
        db.session.commit()

        print("{}: Deactivate contract {}".format(gts(), contract.id))
    else:
        print('contract not found')

    return 'ok'


@app.route('/', methods=['GET'])
def index():
    return 'waiting for the thunder!'


def tasks():
    try:
        contracts = Contract.query.filter_by(active=True).all()

        for contract in contracts:
            if contract.login and contract.password:
                print("Requesting data for {}".format(contract.id))
                if time.time() - contract.last_access_request > 60 * 29 or not contract.access_token:
                    access = ctrack_api.get_tokens(contract.login, contract.password)

                    if access:
                        contract.access_token = access
                        contract.last_access_request = int(time.time())
                        db.session.commit()
                    else:
                        if not contract.error_sent:
                            contract.error_sent = True
                            send_auth_request(contract.id)

                        continue

                new_data = ctrack_api.get_data(contract.access_token, last_id=contract.last_id)
                contract_info = medsenger_api.get_patient_info(contract.id)
                start_date = datetime.datetime.strptime(contract_info['start_date'], "%Y-%m-%d")

                print("Got data for {}".format(contract.id))
                print(new_data)

                max_time = 0
                max_id = -1

                last_minute = 70
                for item in new_data:
                    timestamp = datetime.datetime.strptime(item['measured_dt'][:19], "%Y-%m-%dT%H:%M:%S")
                    timestamp += datetime.timedelta(hours=-4)

                    if timestamp.timestamp() > max_time:
                        max_time = timestamp
                        max_id = item['id']

                    if timestamp < start_date:
                        continue

                    if last_minute == timestamp.minute // 10:
                        continue
                    else:
                        last_minute = timestamp.minute // 10

                    medsenger_api.add_record(contract.id, 'temperature', item['temperature'], timestamp.timestamp())

                if new_data:
                    contract.last_id = max_id

        db.session.commit()
    except Exception as e:
        print(e)


def receiver():
    while True:
        tasks()


def send_auth_request(contract_id):
    medsenger_api.send_message(contract_id,
                               text="Для автоматического импорта данных с термометра C-Track необходимо авторизоваться.",
                               only_patient=True, action_link='auth', action_onetime=True,
                               action_name="Подключить C-Track")


@app.route('/settings', methods=['GET'])
@verify_get
def settings():
    key = request.args.get('api_key', '')

    contract_id = int(request.args.get('contract_id'))
    query = Contract.query.filter_by(id=contract_id)
    if query.count() != 0:
        contract = query.first()
    else:
        return "<strong>Ошибка. Контракт не найден.</strong> Попробуйте отключить и снова подключить интеллектуальный агент к каналу консультирвоания. Если это не сработает, свяжитесь с технической поддержкой."

    return render_template('settings.html', contract=contract, error='')


@app.route('/settings', methods=['POST'])
@verify_get
def settings_save():
    contract_id = int(request.args.get('contract_id'))
    query = Contract.query.filter_by(id=contract_id)
    if query.count() != 0:
        # TODO: check login
        contract = query.first()
        login = request.form.get('login')
        password = request.form.get('password')

        if login and password:
            access = ctrack_api.get_tokens(login, password)

            if access:
                contract.login = login
                contract.password = password
                contract.access_token = access
                contract.last_access_request = int(time.time())
                contract.error_sent = False

                db.session.commit()

                medsenger_api.send_message(contract_id, "Термометр C-Track успешно подключен. Теперь измерения температуры будут поступать автоматически.", only_doctor=True, need_answer=False)
                medsenger_api.send_message(contract_id,
                                           "Термометр C-Track успешно подключен. Теперь, если телефон с установленным мобильным приложением C-Track включен и находится недалеко от пациента, измерения температуры будут поступать автоматически.",
                                           only_patient=True)

                return """
                        <strong>Спасибо, окно можно закрыть</strong><script>window.parent.postMessage('close-modal-success','*');</script>
                        """
            else:
                return render_template('settings.html', contract=contract, error='Не удается войти с таким логином и паролем.')

        else:
            return render_template('settings.html', contract=contract, error='Заполните все поля')

    else:
        return "<strong>Ошибка. Контракт не найден.</strong> Попробуйте отключить и снова подключить интеллектуальный агент к каналу консультирвоания. Если это не сработает, свяжитесь с технической поддержкой."


@app.route('/auth', methods=['GET'])
def auth():
    return settings()


@app.route('/auth', methods=['POST'])
def auth_save():
    return settings_save()


@app.route('/message', methods=['POST'])
def save_message():
    return "ok"


if __name__ == "__main__":
    t = Thread(target=receiver)
    t.start()

    app.run(port=PORT, host=HOST)
