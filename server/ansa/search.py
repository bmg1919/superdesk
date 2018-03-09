
import math
import arrow
import requests
import superdesk

from urllib.parse import urljoin
from flask import current_app as app
from superdesk.io.commands.update_ingest import update_renditions


SEARCH_ENDPOINT = 'ricerca.json'
DETAIL_ENDPOINT = 'detail.json'
ORIGINAL_ENDPOINT = 'binary/{}.jpg?guid={}&username={}&password={}'

THUMB_HREF = 'https://ansafoto.ansa.it/portaleimmagini/bdmproxy/{}.jpg?format=thumb&guid={}'
VIEWIMG_HREF = 'https://ansafoto.ansa.it/portaleimmagini/bdmproxy/{}.jpg?format=med&guid={}'

SEARCH_USERNAME = 'angelo2'
SEARCH_PASSWORD = 'blabla'

ORIG_USERNAME = SEARCH_USERNAME
ORIG_PASSWORD = SEARCH_PASSWORD

TIMEOUT = (5, 25)


def get_meta(doc, field):
    try:
        return doc['metadataMap'][field]['fieldValues'][0]['value']
    except KeyError:
        return None


def ansa_photo_api(endpoint):
    return urljoin(app.config['ANSA_PHOTO_API'], endpoint)


class AnsaPictureProvider(superdesk.SearchProvider):

    label = 'ANSA Pictures'

    def find(self, query):

        size = int(query.get('size', 25))
        page = math.ceil((int(query.get('from', 0)) + 1) / size)

        params = {
            'username': SEARCH_USERNAME,
            'password': SEARCH_PASSWORD,
            'pgnum': page,
            'pgsize': size,
            'querylang': 'ITA',
            'order': 'desc',
            'changets': 'true',
        }

        query_string = query.get('query', {}).get('filtered', {}).get('query', {}).get('query_string', {})
        if query_string.get('query'):
            params['searchtext'] = query_string.get('query')

        response = requests.get(ansa_photo_api(SEARCH_ENDPOINT), params=params, timeout=TIMEOUT)
        return self._parse_items(response)

    def _parse_items(self, response):
        if not response.status_code == requests.codes.ok:
            response.raise_for_status()

        items = []
        json_data = response.json()
        documents = json_data.get('renderResult', {}).get('documents', [])
        for doc in documents:
            md5 = get_meta(doc, 'orientationMD5')
            guid = get_meta(doc, 'idAnsa')
            pubdate = arrow.get(get_meta(doc, 'pubDate_N')).datetime
            items.append({
                'type': 'picture',
                'pubstatus': get_meta(doc, 'status').replace('stat:', ''),
                '_id': guid,
                'guid': guid,
                'headline': get_meta(doc, 'title_B'),
                'description_text': get_meta(doc, 'description_B'),
                'byline': get_meta(doc, 'contentBy'),
                'firstcreated': pubdate,
                'versioncreated': pubdate,
                'creditline': get_meta(doc, 'creditline'),
                'source': get_meta(doc, 'creditline'),
                'renditions': {
                    'thumbnail': {
                        'href': VIEWIMG_HREF.format(md5, guid),
                        'mimetype': 'image/jpeg',
                        'height': 256,
                        'width': 384,
                    },
                    'viewImage': {
                        'href': VIEWIMG_HREF.format(md5, guid),
                        'mimetype': 'image/jpeg',
                        'height': 256,
                        'width': 384,
                    },
                    'baseImage': {
                        'href': ansa_photo_api(ORIGINAL_ENDPOINT).format(md5, guid, ORIG_USERNAME, ORIG_PASSWORD),
                        'mimetype': 'image/jpeg',
                    },
                    'original': {
                        'href': ansa_photo_api(ORIGINAL_ENDPOINT).format(md5, guid, ORIG_USERNAME, ORIG_PASSWORD),
                        'mimetype': 'image/jpeg',
                    },
                },
                'place': [
                    {'name': get_meta(doc, 'city')},
                    {'name': get_meta(doc, 'ctrName')},
                ],
            })
        return items

    def fetch(self, guid):
        params = {
            'idAnsa': guid,
            'username': SEARCH_USERNAME,
            'password': SEARCH_PASSWORD,
            'changets': 'true',
        }

        response = requests.get(ansa_photo_api(DETAIL_ENDPOINT), params=params, timeout=TIMEOUT)
        items = self._parse_items(response)
        item = items[0]

        # generate renditions
        original = item.get('renditions', {}).get('original', {})
        if original:
            update_renditions(item, original.get('href'), {})

        # it's in superdesk now, so make it ignore the api
        item['fetch_endpoint'] = ''
        return item

    def fetch_file(self, href, rendition, item):
        return app.media.get(rendition.get('media'))


def init_app(app):
    superdesk.register_search_provider('ansa', provider_class=AnsaPictureProvider)