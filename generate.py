import json
import time
import requests
import base64
from PIL import Image
import config

class Text2ImageAPI:
    def __init__(self, url, api_key, secret_key):
        self.URL = url
        self.AUTH_HEADERS = {
            'X-Key': f'Key {api_key}',
            'X-Secret': f'Secret {secret_key}',
        }
        

    def get_model(self):
        response = requests.get(self.URL + 'key/api/v1/models', headers=self.AUTH_HEADERS)
        data = response.json()
        return data[0]['id']
    
    def generate(self, prompt, model, images=1):
        params = {
            "type": "GENERATE",
            "numImages": images,
            "width": config.WIDTH,
            "height": config.HEIGHT,
            "style" : config.STYLE,
            "negativePromptUnclip" : 'лица, люди, знаменитости, личности, человек, профиль',
            "generateParams": {
                "query": f"{prompt}"
            }
        }
        data = {
            'model_id': (None, model),
            'params': (None, json.dumps(params), 'application/json')
        }
        response = requests.post(self.URL + 'key/api/v1/text2image/run', headers=self.AUTH_HEADERS, files=data)
        data = response.json()
        return data['uuid']
    
    def check_generation(self, request_id, attempts=10, delay=10):
        while attempts > 0:
            response = requests.get(self.URL + 'key/api/v1/text2image/status/' + request_id, headers=self.AUTH_HEADERS)
            data = response.json()
            if data['status'] == 'DONE':
                if data['censored']:
                    return False
                return data['images']
            attempts -= 1
            time.sleep(delay)
        else:
            print("Время ожидания истекло")
            return False

async def generate_image_by_title(title):
    api = Text2ImageAPI('https://api-key.fusionbrain.ai/', config.BRAIN_API_KEY, config.BRAIN_SECRET_KEY)
    model_id = api.get_model()
    uuid = api.generate(f"Изображение к статье с названием {title}", model_id)
    images = api.check_generation(uuid)
    if images == False:
        return False
    image_base64 = images[0]
    image_data = base64.b64decode(image_base64)
    with open(f"images/image.jpg", "wb") as file:
        file.write(image_data)
    if config.WATERMARK != 'off':
        add_watermark(config.WATERMARK)
    return True

async def generate_image_by_first_p(first_p):
    api = Text2ImageAPI('https://api-key.fusionbrain.ai/', config.BRAIN_API_KEY, config.BRAIN_SECRET_KEY)
    model_id = api.get_model()
    uuid = api.generate(f"Изображение к статье первый абзац которой {first_p}", model_id)
    images = api.check_generation(uuid)
    if images == False:
        return False
    image_base64 = images[0]
    image_data = base64.b64decode(image_base64)
    with open(f"images/image.jpg", "wb") as file:
        file.write(image_data)
    if config.WATERMARK != 'off':
        add_watermark(config.WATERMARK)
    return True

def add_watermark(watermark_filename):
    base_image = Image.open('images/image.jpg')
    watermark = Image.open(watermark_filename)

    base_image.paste(watermark, (20,10), mask=watermark)
    base_image.save('images/image.jpg')
