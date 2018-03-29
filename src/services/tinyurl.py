from .service import Service


class TinyURL(Service):

    def shorten(self, url):
        url_shortened = self.get_request(url)

        return url_shortened
