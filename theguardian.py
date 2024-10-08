import re
from datetime import datetime
import pytz
import config
from getcontent import get_content, replace_hashtag, edit_text, translate_text, get_first_paragrapth


class TG():
    #Удаление парметров
    def delete_param(self, url):
        match = re.match(r'([^?]*)\?', url)
        if match:
            return match.group(1)
        else:
            return url

    #Получение всех ссылок с категории
    def get_href(self, url):
        soup = get_content(url)
        if soup == -1:
            return -1
        section = soup.find(id=re.compile(r'^container-'))
        links = section.find_all('a')
        all_url = []
        for url in links:
            url = self.delete_param(url['href'])
            if "instagram.com" in url:
                continue
            all_url.append(f"https://www.theguardian.com{url}")  
        return all_url

    #Получение названия поста
    def get_title(self, soup):
        if soup == -1:
            return
        
        title = soup.title.string.split('|')[0].strip()
        return title
    
    def get_image(self, url):
        return f"{url}#img-1"

    #Получение хэштегов
    def get_tags(self, soup):
        if soup == -1:
            return
        res = []
        
        tags = soup.find(class_='dcr-1jl528t')
        if tags:
            tags = tags.find_all('a')
        else:
            return res
        include = False
        for tag in tags:
            tag_text = tag.text
            if config.INCLUDE == "on":
                if tag_text in config.INCLUDE_LIST:
                    include = True
            if config.EXCLUDE != "off":
                if tag_text in config.EXCLUDE:
                    return -1
            if config.REPLACMENT != "":
                tag = replace_hashtag(tag_text)
                if tag != '':
                    res.append("#" + tag.replace(" ", "_"))
        if config.SOURCE_TAG == "on":
            res.append("#TheGuardian")
        if config.INCLUDE == "on" and not include:
            return -1     
        return res

    #Получение текста со страницы
    def get_text(self, soup):
        res = ""
        div = soup.find('div', id='maincontent')
        if not div:
            return -1
        paragraphs = div.find_all('p')
        for paragraph in paragraphs:
            #Удаление цитат
            if paragraph.find_parent(['blockquote']) is not None:
                continue
            if 'editor’s note:' in paragraph.text.lower() or 'related article' in paragraph.text.lower():
                continue
            paragraph_text = ''
            for element in paragraph.contents:
                #Удаление ссылок
                if element.name == 'a':  
                    paragraph_text += element.text  
                elif isinstance(element, str):  
                    paragraph_text += element 
                elif element.name == 'span':
                    continue

            #Удаление пустых абзацев
            if paragraph_text == "" or paragraph_text == ' ':
                continue
            res += paragraph_text.strip() + '\n\n'
        res = translate_text(res)
        return(res)

    def check_is_it_today_news(self, soup):
        if soup.find(id="key-events-carousel"):
            return False
        date = soup.find(class_="dcr-1pexjb9")
        if date.find(class_="dcr-u0h1qy"):
            date = date.find(class_="dcr-u0h1qy").text
        else:
            date = date.text
        date = date[:-10].strip()
        date_obj = datetime.strptime(date, "%a %d %b %Y")
        today = datetime.today()
        if today.day == date_obj.day and today.month == date_obj.month:
            return True
        return False

    #Вызов всех функций и формирование сообщения
    def get_page(self, url):
        res = {}
        soup = get_content(url)
        if soup == -1:
            return -1
        if soup == -2:
            return -2
        page = ""
        if not self.check_is_it_today_news(soup):
            return -2
        if config.HEADER != "":
            page += config.HEADER + "\n\n"
        title = translate_text(self.get_title(soup))
        res['title'] = title
        page += "<b>" + title + "</b>"
        #Добавление хэштегов
        if config.HASHTAG == "on":
            tags = self.get_tags(soup)
            if tags == -1:
                return -2
            if len(tags) > 0:
                page += '\n' + ", ".join(tags)
        text = self.get_text(soup)
        if text == -1:
            return -1
        res['first_p'] = get_first_paragrapth(text)
        page += "\n\n" + text
        if config.EXCLUDE_TEXT:
            for bad_word in config.EXCLUDE_TEXT:
                if bad_word.lower() in text.lower():
                    return -2
        page = edit_text(page) + "\n"
        #Добавление дополнительного текста
        if config.FIRST_TEXT != "":
            if config.FIRST_TEXT_URL == "":
                page += "\n<b>" + config.FIRST_TEXT + "</b>\n"
            else:
                page += f'\n<b><a href="{config.FIRST_TEXT_URL}">{config.FIRST_TEXT}</a></b>\n'
        if config.SECOND_TEXT != "":
            if config.SECOND_TEXT_URL == "":
                page += "\n" + config.SECOND_TEXT + "\n"
            else:
                page += f'\n<a href="{config.SECOND_TEXT_URL}">{config.SECOND_TEXT}</a>' + "\n"
        res['page'] = page 
        return res
    
    def get_last_title(self, url):
        soup = get_content(url)
        div = soup.find(class_='dcr-16c50tn').find('h3')
        return div.text