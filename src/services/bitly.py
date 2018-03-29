import json

from .service import Service


class Bitly(Service):

    def shorten(self, url):
        response = self.get_request(url)
        data = json.loads(response)
        url_shortened = data['data']['url']

        return url_shortened

    def formatted_api_url(self):
        return "{}{}{}".format(self.api_url, self.api_key, "&longUrl=")
