import json
import requests
from datetime import date

# Определяем тело адреса API яндекс
HOST = 'https://api.direct.yandex.com/json/v5/'


class YadirectAPI:
    def __init__(self, login, token):
        self.headers = {
            'Authorization': 'Bearer ' + token,
            'Accept-Language': 'ru',
            'Client-Login': login
        }

    def add(self, your_json):
        if isinstance(your_json, dict):
            raw_json = your_json
        else:
            raw_json = json.load(your_json)
        data = raw_json['data']

        def request(href,obj_data):
            try:
                results = requests.post(HOST+href,obj_data,headers=self.headers)
                if results.status_code != 200 or results.json().get("error", False):
                    error = "Код ошибки {}".format(results.json()["error"]["error_code"])
                    print(error)
                else:
                    print("ОК. Информация о баллах: {}".format(results.headers.get("Units")))
                    return results.json()
            except ConnectionError:
                print("Ошибка соединения с сервером")
            except:
                print("Непредвиденная ошибка")

        def create_campaigns():
            # Получаем информацию о компании из JSON файла
            campaign = data[0]['campaign']
            # Выставляем дату начала комании
            if campaign['StartDate'] == "null":
                campaign['StartDate'] = date.today()
            campaigns_body = {"method": "add",
                              "params": {"Campaigns": [campaign]}}
            # Подготавливаем JSON для запроса
            body_json = json.dumps(campaigns_body)
            # Отправляем запрос на сервер
            push = request('campaigns/',body_json)

            return push

        # Создаем группы
        def create_groups():
            # Сюда будем собирать все группы из файла
            groups = []
            # Получаем ID компании
            campaign_id = create_campaigns()['result']['AddResults'][0]['Id']
            for item in raw_json['data']:
                # Получаем объекты групп из файла
                group = item['adgroup']
                # Присваеваем объектам ID компании
                group['CampaignId'] = campaign_id
                # Отправляем объекты в список
                groups.append(group)
            # Определяем структуру запроса
            groups_body = {"method": "add",
                           "params": {"AdGroups": groups}}
            # Подготавливаем JSON для запроса
            body_json = json.dumps(groups_body)
            # Отправляем запрос на сервер
            push = request('adgroups/', body_json)
            return push

        # Создаем объявления
        def create_ads():
            # Здесь все аналогично, только итераций больше
            groups_ids = create_groups()['result']['AddResults']
            for i in range(len(groups_ids)):
                data[i]['ad']['AdGroupId'] = groups_ids[i]['Id']
            ads = []
            for item in data:
                ads.append(item['ad'])
            ads_body = {"method": "add",
                        "params": {"Ads": ads}}
            ads_json = json.dumps(ads_body)
            request('ads/', ads_json)
            return groups_ids

        # Отправка ключевых слов
        def add_keywords():
            group_ids = create_ads()
            keywords = []

            # Все тоже самое кроме этой функции. Из-за ограничения в 1000 ключевых слов в запросе,
            # ниже мы отлавливаем размер списка. При его наполнении мыотравляем запрос.
            def pull_keywords():
                keywords_body = {"method": "add",
                                 "params": {"Keywords": keywords}}
                keywords_json = json.dumps(keywords_body)
                push = request('keywords/', keywords_json)
                return push

            for i in range(len(group_ids)):
                for item in data[i]['keywords']:
                    item["AdGroupId"] = group_ids[i]['Id']
                    if item["Bid"] == "null":
                        item["Bid"] = 1000000
                    keywords.append(item)
                    # Отлов происходит здесь.
                    if len(keywords) == 999:
                        pull_keywords()
                        # После отправки запроса, список очищается и начинает заполняться заново.
                        del keywords[:]
            return pull_keywords()

        return add_keywords()


