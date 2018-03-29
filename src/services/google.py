import json

from .service import Service


class Google(Service):

    def shorten(self, url):
        post_data = json.dumps({'longUrl': url}).encode('utf-8')
        data = self.post_request(post_data)
        url_shortened = data['id']

        return url_shortened

    def formatted_api_url(self):
        return "{}{}".format(self.api_url, self.api_key)
