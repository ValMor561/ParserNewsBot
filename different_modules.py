import config
from getcontent import get_content
from cnn import CNN

def choise_module(url):
    if "edition.cnn" in url:
        return CNN()
    
#Получение времени последнего поста
def get_title():
    res = "Названия последних постов:\n"
    for url in config.SOURCES.keys():
        PM = choise_module(url)
        soup = get_content(url)
        title = PM.get_last_title(soup)
        res += f'{url} - {title}\n'
    return res
