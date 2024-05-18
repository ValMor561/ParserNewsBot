import psycopg2
import config

#Класс для подключения к базе данных
class BDRequests():

    #Установка соединения
    def __init__(self):
        self.connection = psycopg2.connect(
            host=config.HOST,
            database=config.DATABASE,
            user=config.USER,
            password=config.PASSWORD
        )

    #Закрытие соединения
    def __del__(self):
        self.connection.close()

    #Добавление ссылки в таблицу
    def insert_url(self, url):
        cursor = self.connection.cursor()
        insert_query = f'INSERT INTO public."{config.TABLENAME}" (url) VALUES (%s);'
        cursor.execute(insert_query, (url,))
        self.connection.commit()

    #Очистка таблицы
    def clear_database(self):
        cursor = self.connection.cursor()
        delete_query = f'DELETE FROM public."{config.TABLENAME}";'
        cursor.execute(delete_query)
        self.connection.commit()

    #Проверка хранится ли ссылка в таблице
    def check_url_exist(self, url):
        cursor = self.connection.cursor()
        cursor.execute("SELECT check_url_exists(%s, %s)", (url, config.TABLENAME))
        result = cursor.fetchone()[0]
        return result
