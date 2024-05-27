import config
from getcontent import get_content
from cnn import CNN
from buissnesinsider import BI

def choise_module(url):
    if "edition.cnn" in url:
        return CNN()
    if "businessinsider" in url:
        return BI()
    
#Получение времени последнего поста
def get_title():
    res = "Названия последних постов:\n"
    for url in config.SOURCES.keys():
        PM = choise_module(url)
        title = PM.get_last_title(url)
        res += f'{url} - {title}\n'
    return res
