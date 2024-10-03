from aiogram import types,  Router, Bot, Dispatcher, F
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.enums.parse_mode import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.exceptions import TelegramRetryAfter, TelegramBadRequest, TelegramNetworkError, TelegramForbiddenError
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram.types import FSInputFile
import asyncio
import datetime
import pytz
import os
import sys
from different_modules import get_title, choise_module
from generate import generate_image_by_first_p, generate_image_by_title
import config
import bd

bot = Bot(token=config.BOT_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher(storage=MemoryStorage())
router = Router()
BD = bd.BDRequests()
RUNNING = True
IS_ERROR = False

#Функия для запуска парсинга с проверкой по времени
async def run_bot():
    now = datetime.datetime.now(pytz.timezone('Europe/Moscow'))
    all_week_days = ["понедельник", "вторник", "среда", "четверг", "пятница", "суббота", "воскресенье"]
    current_day = now.weekday()
    global IS_ERROR
    if os.path.exists("settings/restart.txt"):
        with open("settings/restart.txt", 'r') as file:
            id = file.read().strip()
            await bot.send_message(id, "Бот запущен")
        os.remove("settings/restart.txt")
    SCHEDULER = AsyncIOScheduler(timezone='Europe/Moscow')
    if all_week_days[current_day] in config.WORK_DAYS:
        if config.WORK_PERIOD != "off":
            try:
                SCHEDULER.add_job(check_urls, trigger='interval', minutes=int(config.WORK_PERIOD))
                SCHEDULER.add_job(check_urls, trigger='date', next_run_time=datetime.datetime.now() + datetime.timedelta(seconds=10))
            except Exception as e:
                print(e)
                IS_ERROR = True
        if config.WORK_TIME[0] != "off":
            for time in config.WORK_TIME:
                try:
                    time = time.strip()
                    hour, minute = time.split(":")
                    SCHEDULER.add_job(check_urls, trigger='cron', day="*", hour=hour, minute=minute)
                except Exception as e:
                    print(e)
                    IS_ERROR = True              
    SCHEDULER.start()

def save_current_time_to_file():
    with open("settings/time.txt", 'w') as file:
        current_time = datetime.datetime.now().strftime("%H:%M:%S %Y-%m-%d")
        file.write(current_time)

#Ограничение доступа пользователям, которых нет в списке
@router.message(lambda message:str(message.from_user.id) not in config.ADMINS, F.chat.type == 'private')
async def check_user_id(msg: Message):
    await msg.answer("Нет доступа")
    return

async def check_urls():
    now = datetime.datetime.now(pytz.timezone('Europe/Moscow'))
    current_time = now.strftime("%H:%M")
    if not (config.WORK_START_TIME <= current_time <= config.WORK_END_RIME):
        return
    #Переменная для остановки
    global RUNNING
    global IS_ERROR
    RUNNING = True
      
    sources = config.CATEGORIES
    for index, row in sources.iterrows():
        if config.LIMIT_POST == "*" or config.LIMIT_POST == "off":
            session_count = -2
        else:
            session_count = int(config.LIMIT_POST)
        row = row.fillna("")
        urls = config.get_multiple_values(row['Urls'])
        channels_id = config.get_multiple_values(row['Channels'])
        config.FIRST_TEXT = str(row['First_text'])
        config.FIRST_TEXT_URL = str(row['First_url'])
        config.SECOND_TEXT = str(row['Second_text'])
        config.SECOND_TEXT_URL = str(row['Second_url'])
        for url in urls:
            PM = choise_module(url)
            #Получение ссылок из категории
            URLS = PM.get_href(url)
            if URLS == -1 or URLS == -2:
                continue
            for URL in URLS:
                if not RUNNING:
                    return False
                #Отсев дублей
                if BD.check_url_exist(URL):
                    continue
                
                if session_count != -2:
                    if session_count == 0:
                        continue
                
                #Получение текста
                try:
                    dict = PM.get_page(URL)
                except Exception as e:
                    print(e)
                    continue
                if dict == -1:
                    continue  
                elif dict == -2:
                    BD.insert_url(URL)
                    continue
                
                text = dict['page']
                if config.IMAGE == 'on':
                    photo = await get_photo(dict['title'], dict['first_p'], URL, PM)
                else:
                    photo = -2
                BD.insert_url(URL)
                if photo == -1:
                    print(f"Новость пропущена из-за отсутсвия картинки {URL}")
                    continue
                #Отправка в канал
                count = 0
                for channel in channels_id:
                    if count == 15:
                        await asyncio.sleep(5)
                    if config.IMAGE == 'on':
                        try:
                            success = await send_post_with_photo(photo, text, channel)
                            count += success
                        except Exception as e:
                            print(e)
                            continue
                    else:
                        try:
                            success = await send_text_post(text, channel)
                            count += success
                        except Exception as e:
                            print(e)
                            continue
                save_current_time_to_file()
                session_count -= 1
    return True

async def get_photo(title, first_p, url, PM):
    if config.GENERATE_IMAGE == 'on':
        try:
            success = await generate_image_by_first_p(first_p)
            if success:
                photo = FSInputFile("images/image.jpg")
                return photo
            else: 
                success = await generate_image_by_title(title)
                if success:
                    photo = FSInputFile("images/image.jpg")
                    return photo
        except Exception as e:
            print(str(e))
    photo = PM.get_image(url)
    return photo

async def send_post_with_photo(photo, text, channel):
    try:
        await bot.send_photo(channel, photo, parse_mode='html', caption=text)
        count = 1
    except TelegramRetryAfter as e:
        count = 0
        await asyncio.sleep(e.retry_after)
        await bot.send_photo(channel, photo, parse_mode='html', caption=text)
    except TelegramNetworkError as e:
        count = 0
        await asyncio.sleep(15)
        await bot.send_photo(channel, photo, parse_mode='html', caption=text)
    return count

async def send_text_post(text, channel):
    try:
        await bot.send_message(text=text, parse_mode='html', chat_id=channel)
        count = 1
    except TelegramRetryAfter as e:
        count = 0
        await asyncio.sleep(e.retry_after)
        await bot.send_message(text=text, parse_mode='html', chat_id=channel)
    except TelegramNetworkError as e:
        count = 0
        await asyncio.sleep(15)
        await bot.send_message(text=text, parse_mode='html', chat_id=channel)
    return count

#Функция парсинга запускается командой post либо по расписанию функцией run_bot
@router.message(Command("post"))
async def start_handler(msg: Message):
    global IS_ERROR
    await msg.answer("Начат обход ссылок")
    try:
        if await check_urls():
            await msg.answer("Все ссылки проверены")
    except Exception as e:
        print(e)
        await msg.answer("В процессе работы возникли ошибки, для перезапуска /restart")
        IS_ERROR = True     

#Запуск бота и вход в режим бесконечного цикла
@router.message(Command("start"))
async def cmd_start(msg: Message):
    global RUNNING
    RUNNING = True
    #Добавление кнопок
    builder = ReplyKeyboardBuilder()
    builder.row(types.KeyboardButton(text='/post', callback_data='post'), types.KeyboardButton(text='/stop', callback_data='stop'))
    builder.row(types.KeyboardButton(text='/clean_bd', callback_data='clean_bd'), types.KeyboardButton(text='/restart', callback_data='restart'))
    builder.row(types.KeyboardButton(text='/stats', callback_data='stats'), types.KeyboardButton(text='/start', callback_data='start'))

    keyboard = builder.as_markup(resize_keyboard=True)
    await msg.answer("Бот запущен\nКоманды:\n/post - Единоразовый запуск парсера\n/clean_bd - Очистка базы данных с посещенными ссылками\n/restart - Перезапуск всего бота\n/stop - Остановка функции парсинга\n/stats - Состояние бота", reply_markup=keyboard)

    
#Очистка базы данных с ссылками
@router.message(Command("clean_bd"))
async def clear_database(msg: Message):
    BD.clear_database()
    await msg.answer("База данных очищена")

#Остановка функции парсинга
@router.message(Command("stop"))
async def process_callback_stop(msg: Message):
    global RUNNING
    RUNNING = False
    await msg.answer("Обход остановлен")

async def get_last_bot_message_time():
    res = "Время последнего сообщения: "
    with open("settings/time.txt", 'r') as file:
        time_str = file.read().strip()
        res += time_str + "\n"
    return res

#Текущее состояние
@router.message(Command("stats"))
async def process_callback_stop(msg: Message):
    news_time = get_title()
    post_time = await get_last_bot_message_time()
    global IS_ERROR
    if IS_ERROR:
        await msg.answer(f"Возникли ошибки для перезапуска выполните /restart:\n{post_time}{news_time}")
    else:
        await msg.answer(f"Бот работает:\n{post_time}{news_time}")

#Перезапуск бота
@router.message(Command("restart"))
async def restart(msg: Message):
    await msg.answer("Перезапуск бота...\n")
    with open("settings/restart.txt", 'w') as file:
        file.write(str(msg.from_user.id))
    python = sys.executable
    os.execl(python, python, *sys.argv)

