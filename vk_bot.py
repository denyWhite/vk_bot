from tornado.ioloop import IOLoop
from tornado.web import RequestHandler, Application
import json
import vk
import re
import requests

GROUP_ID = "000000"  # ИД группы с ботом
GROUP_DOMAIN = "group_domain"  # буквенное обозначение сообщества (то, что следует после vk.com)
CONFIRMATION_STRING = "confirmation_string"  # Строка для подтверждения сервера Callback API
SECRET_KEY = "secret_key"  # Секретный ключ Callback API
# Токен авторизации https://vk.com/dev/authcode_flow_group
TOKEN = "tokentokentoken"


class MainHandler(RequestHandler):
    def _message_new(self, dct):
        """
        Реакция на новое сообщение
        :param dct: JSON от Callback API
        :return: bool удалось ли ответить
        """
        global answer
        request = dct["object"]["text"].strip()  # Текст сообщения
        peer_id = int(dct["object"]["peer_id"])  # Источник сообщения
        from_id = int(dct["object"]["from_id"])  # Автор сообщения
        user = vk_api.users.get(user_id=from_id) # Получаем инфу от отправителе
        user_first_name = user[0]['first_name'] # Имя пользователя
        # Сообщение прислано в беседу (True) или в сообщения группы (False)
        is_in_conversation = not dct["object"]["from_id"] == dct["object"]["peer_id"]
        # Есть ли обращение к боту
        regx = re.compile(r"\[club{0}\|@{1}\]".format(GROUP_ID, GROUP_DOMAIN))
        is_to_bot = bool(re.match(regx, request))
        if is_to_bot:
            request = re.sub(regx, "", request).strip()

        """
        ВОТ ТУТ ГОТОВИМ ОТВЕТ
        """
        response = "{0}, ты спросил: {1}".format(user_first_name, request)

        vk_api.messages.send(peer_id=peer_id, message=response)  # Отвечаем
        return True

    def _answer(self, dct):
        """
        Основная функция, которая формирует ответные действия
        на события с сервера
        :param dct: JSON от Callback API
        :return: Ответ серверу
        """
        if dct["type"] == "confirmation":  # Запрос на подтверждение сервера
            print("Отправляем подтверждение", CONFIRMATION_STRING)
            return CONFIRMATION_STRING
        elif dct["type"] == "message_new":  # Новое сообщение
            self._message_new(dct)
        else:
            print("Запрос не обработан:", dct)
        return "OK"

    def post(self):
        body = self.request.body.decode('utf-8').strip()  # Получаем тело POST запроса
        answer = "OK"  # Ответ по умолчанию
        try:
            jsn = json.loads(body)  # Пытаемя разобрать JSON
            #print("Json", jsn)
            if jsn["secret"] != SECRET_KEY:  # Проверяем секретный ключ
                raise KeyError("")
            answer = self._answer(jsn)  # Формируем ответ
        except ValueError:
            print("Пришел неизвестный запрос")
        except KeyError:
            print("Проблемы с секретным ключом (не верен, или не передан сервером)")
        self.write(answer)  # Отвечаем



session = vk.Session(access_token=TOKEN)
vk_api = vk.API(session, v="5.85")

app = Application([(r"/", MainHandler)])  # Создаем приложение сервера
app.listen(80)  # Порт, на котором слушаем запросы
try:
    IOLoop.instance().start()
except KeyboardInterrupt:  # Останавливаем сервер по Ctrl+C
    IOLoop.instance().stop()
