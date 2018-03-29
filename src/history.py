import datetime
import json
import os
import urllib.parse
import uuid


class History:
    HISTORY_FILENAME = 'history.json'

    def __init__(self, cache_path):
        self.cache_path = cache_path

    def add(self, long_url, short_url, service_name):
        history = self.get_history_file()
        with open(history, 'r+') as f:
            try:
                data = json.load(f)
            except Exception:
                data = {"items": []}

            history_item = {
                'id': str(uuid.uuid4()),
                'longUrl': urllib.parse.quote_plus(long_url),
                'shortUrl': short_url,
                'service': service_name,
                'date': datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S%z')
            }
            data["items"].insert(0, history_item)
            f.seek(0)
            json.dump(data, f)
            f.truncate()

    def read(self):
        history_file = self.get_history_file()
        with open(history_file, 'r') as file:
            try:
                history = json.load(file)
                if len(history['items']) == 0:
                    history = None
            except Exception:
                history = None

        if history is None:
            return False

        return history

    def remove(self, history_id):
        with open(self.get_history_file(), 'r+') as f:
            data = json.load(f)

            new_data = list(filter(lambda item: item['id'] != history_id, data['items']))
            new_data = {"items": new_data}

            f.seek(0)
            json.dump(new_data, f)
            f.truncate()

    def clear(self):
        with open(self.get_history_file(), 'r+') as f:
            new_data = {"items": []}
            f.seek(0)
            json.dump(new_data, f)
            f.truncate()

    def get_history_file(self):
        return os.path.join(self.cache_path, self.HISTORY_FILENAME)
