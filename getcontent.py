from requests.exceptions import ConnectionError 
from bs4 import BeautifulSoup
from deep_translator import GoogleTranslator
from fake_useragent import UserAgent
import pandas as pd
import re
import random
import requests
import config

def transform_to_http_format(input_string):
    parts = input_string.split(":")
    ip = parts[0]
    port = parts[1]
    login = parts[2] if len(parts) > 2 else ""
    password = parts[3] if len(parts) > 3 else ""
    
    if login and password:
        http_formatted_string = f"http://{login}:{password}@{ip}:{port}"
    else:
        http_formatted_string = f"http://{ip}:{port}"
    
    return http_formatted_string

#Выбор случайного прокси
def get_proxy():
    proxy = random.choice(config.PROXY)   
    https_proxy = transform_to_http_format(proxy)
    proxies = {
        'http' : https_proxy,
        'https': https_proxy
    }
    return proxies

#Получение информации на странице
def get_content(url):
    user_agent = UserAgent().random.strip()
    headers = {'User-Agent': user_agent}
    count_try = 0
    if config.PROXY[0] != "off":
        #Перебор прокси если не получилось подключиться
        while count_try != 15:
            proxies = get_proxy()
            try:
                response = requests.get(url=url, headers=headers, proxies=proxies)
                if response.status_code != 200:
                    print(response.text)
                    print("Прокси не подошла пробую другую")
                    count_try += 1
                else:    
                    break
            except requests.exceptions.ProxyError as e:
                print("Прокси не подошла пробую другую")
                count_try += 1
                print(e)
            except ConnectionError as e:
                count_try += 1
        if count_try == 15:
            print("15 неудачных попыток")
            return -1
    else:
        response = requests.get(url, headers=headers)
            
    if response.status_code == 200:
        html_content = response.text
        soup = BeautifulSoup(html_content, 'html.parser')
        return soup
    else:
        print(response.text)
        return -1

def replace_hashtag(tag):
    if 'csv' in config.REPLACMENT:
        replacements = pd.read_csv(config.REPLACMENT)
    if 'xlsx' in config.REPLACMENT:
        replacements = pd.read_excel(config.REPLACMENT)
    replacements = replacements.fillna("")
    replace_dict = dict(zip(replacements['Tag'], replacements['Replace']))
    for key in replace_dict:
        tag = tag.replace(key, replace_dict[key])
    return tag

#Обработка длинны текста
def edit_text(text):
    if config.TEXT_LENGTH != 1000:
        text = text[0:config.TEXT_LENGTH]
        text += "...\n\n"
        return text
    
    if config.IMAGE == 'on':
        maxlen = 1024 - len(config.FIRST_TEXT) - len(config.FIRST_TEXT_URL) - len(config.SECOND_TEXT) - len(config.SECOND_TEXT_URL) - 40
    else:
        maxlen = 4096 - len(config.FIRST_TEXT) - len(config.FIRST_TEXT_URL) - len(config.SECOND_TEXT) - len(config.SECOND_TEXT_URL) - 40

    if len(text) > maxlen:
        text = text[0:maxlen]
        text = re.sub(r'[^.]*$', '', text)
    return text

def translate_text(text):
    if len(text) > 4900:
        text = text[0:4900]
        text = re.sub(r'[^.]*$', '', text)
    return GoogleTranslator(source='en', target='ru').translate(text)

def get_first_paragrapth(text):
    paragraphs = text.split('\n')
    return paragraphs[0]
