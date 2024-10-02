import configparser
import pandas as pd
#Чтение конфигурационного файла
def get_config(filename):
    config = configparser.ConfigParser()
    config.read(filename, encoding="utf-8")

    return config

#Функция для считывания значений из файла если он указан в качестве параметра, либо из .ini файла
#На вход подается значение хранящееся в конфиге
def get_multiple_values(param):
    if ".txt" in param:
        with open(param, encoding = 'utf-8', mode = 'r') as file:
            lines = file.readlines()
            lines = [line.strip() for line in lines]
            return lines
    return param.replace(" ", "").split(',')

all_week_days = ["понедельник", "вторник", "среда", "четверг", "пятница", "суббота", "воскресенье"]
config = get_config('settings/config2.ini')

#Глобальные переменные всех параметров
BOT_TOKEN = config['BOT_SETTINGS']['bot_token']
ADMINS = get_multiple_values(config['BOT_SETTINGS']['admins'])
PROXY = get_multiple_values(config['PROXY']['proxy'])
WORK_DAYS = all_week_days if config['SETTINGS']['work_days'] == '*' else config['SETTINGS']['work_days'].split(", ")
WORK_START_TIME = config['SETTINGS']['work_start_time']
WORK_END_RIME = config['SETTINGS']['work_end_time']
WORK_TIME = config['SETTINGS']['work_time'].split(',')
WORK_PERIOD = config['SETTINGS']['work_period']
REPLACMENT = config['SETTINGS']['replacement']
EXCLUDE = get_multiple_values(config['SETTINGS']['exclude'])
EXCLUDE_TEXT = get_multiple_values(config['SETTINGS']['exclude_text'])
INCLUDE = config['SETTINGS']['include_work']
INCLUDE_LIST = get_multiple_values(config['SETTINGS']['include_list'])
SOURCE_TAG = config['SETTINGS']['source_tag']
LIMIT_POST = config['SETTINGS']['limit_post']
HASHTAG = config['MESSAGE']['hashtag']
IMAGE = config['MESSAGE']['image']
GENERATE_IMAGE = config['MESSAGE']['generate_image']
TEXT_LENGTH = 1000 if config['MESSAGE']['text_length'] == '*' else int(config['MESSAGE']['text_length'])
HEADER = config['MESSAGE']['header']
HOST = config['BD']['host']
DATABASE = config['BD']['database']
USER = config['BD']['user']
PASSWORD = config['BD']['password']
TABLENAME = config['BD']['tablename']
BRAIN_API_KEY = config['BRAINFUSION']['api_key']
BRAIN_SECRET_KEY = config['BRAINFUSION']['secret_key']
STYLE = config['BRAINFUSION']['style']
WATERMARK = config['BRAINFUSION']['watermark']
WIDTH = int(config['BRAINFUSION']['width'])
HEIGHT = int(config['BRAINFUSION']['height'])
CATEGORIES = pd.read_excel(config['SOURCES']['source_table'])
FIRST_TEXT = ""
FIRST_TEXT_URL = ""
SECOND_TEXT = ""
SECOND_TEXT_URL = ""
