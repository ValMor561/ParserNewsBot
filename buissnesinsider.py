import re
from datetime import datetime
import config
from getcontent import get_content, replace_hashtag, edit_text, translate_text, get_first_paragrapth


class BI():
    #Удаление парметров
    def delete_param(self, url):
        match = re.match(r'([^?]*)\?', url)
        if match:
            return match.group(1)
        else:
            return url

    #Получение всех ссылок с категории
    def get_href(self, start_url):
        soup = get_content(start_url)
        if soup == -1:
            return -1
        divs = soup.find_all(['h2', 'h3'])
        all_url = []
        for div in divs:
            tag = div.find_previous('div', class_='tout-tag')
            title = tag.find('title')
            if title:
                if title.text == "Play Icon":
                    continue
            url = div.find('a')
            url = self.delete_param(url['href'])
            if "businessinsider" not in url:
                url = f"https://www.businessinsider.com{url}"
            all_url.append(url)
        return all_url

    #Получение названия поста
    def get_title(self, soup):
        if soup == -1:
            return
        
        title = soup.find('h1').text
        return title
    
    def get_image(self, url):
        soup = get_content(url)
        img_link = soup.find(class_="aspect-ratio")
        if img_link:
            img_link = img_link.find('img').attrs['src']
            img_link = self.delete_param(img_link)
            return img_link
        return ""

    #Получение хэштегов
    def get_tags(self, soup):
        if soup == -1:
            return
        res = []
        
        tags = soup.find(class_='post-meta')
        if tags:
            tags = tags.find_all('a')
        else:
            return res
        include = False
        for tag in tags:
            tag_text = tag.text.strip()
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
            res.append("#Bitmedia")
        if config.INCLUDE == "on" and not include:
            return -1     
        return res

    #Получение текста со страницы
    def get_text(self, soup):
        res = ""
        paragraphs = soup.find(class_='post-content')
        if not paragraphs:
            return -1
        paragraphs = paragraphs.find_all('p', recursive=True)
        for paragraph in paragraphs:
            #Удаление цитат
            if paragraph.find_parent(['blockquote']) is not None:
                continue
            if 'editor’s note:' in paragraph.text.lower() or 'related stories' in paragraph.text.lower():
                continue
            paragraph_text = ''
            for element in paragraph.contents:
                #Удаление ссылок
                if element.name == 'a':  
                    paragraph_text += element.text  
                elif isinstance(element, str):  
                    paragraph_text += element
                elif element.name == 'span':
                    paragraph_text += element.text  

            #Удаление пустых абзацев
            if paragraph_text == "" or paragraph_text == ' ':
                continue
            res += paragraph_text.strip() + '\n\n'
        res = translate_text(res)
        return(res)

    def check_is_it_today_news(self, soup):
        date = soup.find(class_="byline-timestamp")
        date = date.text.split(",")
        date = date[0].strip()
        date_obj = datetime.strptime(date, '%Y-%m-%dT%H:%M:%SZ')
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
        divs = soup.find_all(['h2', 'h3'])
        for div in divs:
            tag = div.find_previous('div', class_='tout-tag')
            tag = tag.find('a').attrs['href']
            if tag in url:
                return div.text