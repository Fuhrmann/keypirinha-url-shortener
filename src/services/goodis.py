import json

from .service import Service


class GoodIs(Service):
    def shorten(self, url):
        response = self.get_request(url)
        data = json.loads(response)
        url_shortened = data['shorturl']

        return url_shortened
