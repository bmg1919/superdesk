import json
import requests
from flask import current_app as app
from .process_html import process_html

"""
    Translate text from body_html
"""


def translate(text='', **kwargs):
    URL_TRANSLATION = app.config["ANSA_TRANSLATION_URL"]
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    data = {
        'text': text,
        'lang': kwargs.get('lang', 'en'),
        'target': kwargs.get('target', 'it')
    }

    try:
        result = requests.post(URL_TRANSLATION, data=data, headers=headers, timeout=(5, 30))
        response = json.loads(result.text)
        return response.get('translatedtext', text)
    except requests.exceptions.ReadTimeout:
        return text


def translate_text_macro(item, **kwargs):
    lang = 'en' if item.get('language', 'en') == 'en' else 'it'
    target = 'it' if lang == 'en' else 'en'
    item['body_html'] = process_html(item.get('body_html', ''), translate, lang=lang, target=target)

    return item


name = 'Translate text'
label = 'Translate text'
callback = translate_text_macro
access_type = 'frontend'
action_type = 'direct'
simple_replace = True