import json
import urllib.parse
import urllib.request


class Service:
    def __init__(self, api_url, api_key=None):
        self.api_url = api_url
        self.api_key = api_key

    def get_request(self, url):
        api_url = self.formatted_api_url()
        req = urllib.request.Request("{}{}".format(api_url, urllib.parse.quote_plus(url)))

        with urllib.request.urlopen(req) as response:
            return response.read().decode('utf-8')

    def post_request(self, post_data):
        headers = {'Content-Type': 'application/json'}
        req = urllib.request.Request(self.formatted_api_url(), post_data, headers)

        with urllib.request.urlopen(req) as res:
            data = json.load(res)

        return data

    def formatted_api_url(self):
        return self.api_url
