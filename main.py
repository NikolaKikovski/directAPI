import json

import requests

# Указываем входные параметры
LOGIN = 'YOUR_LOIN'
TOKEN = 'YOUR_TOKEN'
FILE = 'PATH_TO_JSON_FILE'


class YandexApi:
    # Определяем тело адреса API яндекс
    HOST = 'https://api.direct.yandex.com/json/v5/'
    # Определяем стандарный header
    headers = {'Authorization': 'Bearer ' + TOKEN,
               'Accept-Language': 'ru',
               'Client-Login': LOGIN}
    # Открываем файл с JSON в нужной кодировке
    with open(FILE, encoding='utf-8') as f:
        raw_json = json.load(f)

    # Создаем компанию
    def create_campaigns(self):
        # Получаем информацию о компании из JSON файла
        campaign = self.raw_json['data'][0]['campaign']
        # Выставляем дату начала комании
        campaign['StartDate'] = '2018-09-01'
        # Определяем структуру запроса
        campaigns_data = {"method": "add",
                          "params": {"Campaigns": [campaign]}}
        # Подготавливаем JSON для запроса
        prepare_json = json.dumps(campaigns_data)
        # Отправляем запрос на сервер
        pull = requests.post(self.HOST+'campaigns/', prepare_json, headers=self.headers)
        # Получаем ответ сервера
        result = pull.json()
        # Получаем ID созданной компании
        campaign_id = result['result']['AddResults'][0]['Id']
        # Возвращаем ID
        return campaign_id
    # Создаем группы

    def create_groups(self):
        # Сюда будем собирать все группы из файла
        groups = []
        # Получаем ID компании
        campaign_id = self.create_campaigns()
        for item in self.raw_json['data']:
            # Получаем объекты групп из файла
            group = item['adgroup']
            # Присваеваем объектам ID компании
            group['CampaignId'] = campaign_id
            # Отправляем объекты в список
            groups.append(group)
        # Определяем структуру запроса
        groups_data = {"method": "add",
                       "params": {"AdGroups": groups}}
        # Подготавливаем JSON для запроса
        prepare_json = json.dumps(groups_data)
        # Отправляем запрос на сервер
        pull = requests.post(self.HOST+'adgroups/', prepare_json, headers=self.headers)
        # Получаем ответ сервера
        result = pull.json()
        # Получаем ID созданных групп
        groups_id = result['result']['AddResults']
        # Возвращаем ID
        return groups_id

    # Создаем объявления
    def create_ads(self):
        # Здесь все аналогично, только итераций больше
        groups_ids = self.create_groups()
        ads_raw = self.raw_json['data']
        for i in range(len(groups_ids)):
            ads_raw[i]['ad']['AdGroupId'] = groups_ids[i]['Id']
        ads = []
        for item in ads_raw:
            ads.append(item['ad'])
        ads_data = {"method": "add",
                    "params": {"Ads": ads}}
        prepare_json = json.dumps(ads_data)
        pull = requests.post(self.HOST+'ads/', prepare_json, headers=self.headers)
        pull.json()
        return groups_ids

    # Отправка ключевых слов
    def add_keywords(self):
        group_ids = self.create_ads()
        keyword_raw = self.raw_json['data']
        keywords = []

        # Все тоже самое кроме этой функции. Из-за ограничения в 1000 ключевых слов в запросе,
        # ниже мы отлавливаем размер списка. При его наполнении мыотравляем запрос.
        def pull_keywords():
            keywords_data = {"method": "add",
                             "params": {"Keywords": keywords}}
            prepare_json = json.dumps(keywords_data)
            pull = requests.post(self.HOST + 'keywords/', prepare_json, headers=self.headers)
            result = pull.json()
            return result

        for i in range(len(group_ids)):
            for z in keyword_raw[i]['keywords']:
                z["AdGroupId"] = group_ids[i]['Id']
                z["Bid"] = 1000000
            for item in keyword_raw[i]['keywords']:
                keywords.append(item)
                # Отлов происходит здесь.
                if len(keywords) == 999:
                    pull_keywords()
                    # После отправки запроса, список очищается и начинает заполняться заново.
                    del keywords[:]
        return pull_keywords()


api = YandexApi()
print(api.add_keywords())
