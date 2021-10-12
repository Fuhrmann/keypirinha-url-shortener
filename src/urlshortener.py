# Keypirinha launcher (keypirinha.com)

import re
import traceback
from urllib.error import HTTPError
from urllib.parse import unquote

import keypirinha as kp
import keypirinha_util as kpu

from .history import History
from .services.bitly import Bitly
from .services.goodis import GoodIs
from .services.tinyurl import TinyURL
from .services.shlink import Shlink

class URLShortener(kp.Plugin):
    # The keypirinha's category that represents a shortened URL
    ITEM_URL = kp.ItemCategory.USER_BASE + 1

    # The keypirinha's category that represents a entry in the user's history
    ITEM_HISTORY = kp.ItemCategory.USER_BASE + 2
    services = {
        'tinyurl': TinyURL,
        'isgood': GoodIs,
        'bitly': Bitly,
        'shlink': Shlink,
    }

    # Default service used to shorten urls
    DEFAULT_MAIN_SERVICE = 'tinyurl'

    def __init__(self):
        super().__init__()
        self.service_name = None
        self.main_service = None
        self.history_enabled = None
        self.historian = History(self.get_package_cache_path(True))

    def on_start(self):
        self._read_config()
        self._create_actions()

    def on_catalog(self):
        catalog = [self.create_item(
            category=kp.ItemCategory.KEYWORD,
            label='URL Shortener',
            short_desc='Shorten an URL and copy the result',
            target='urlshortener',
            args_hint=kp.ItemArgsHint.REQUIRED,
            hit_hint=kp.ItemHitHint.NOARGS
        )]

        if self.history_enabled:
            catalog.append(self.create_item(
                category=kp.ItemCategory.KEYWORD,
                label='URL Shortener: History',
                short_desc='See the history of your shortened links',
                target='urlshortenerhistory',
                args_hint=kp.ItemArgsHint.REQUIRED,
                hit_hint=kp.ItemHitHint.NOARGS
            ))

            catalog.append(self.create_item(
                category=kp.ItemCategory.KEYWORD,
                label='URL Shortener: Clear history',
                short_desc='Remove all shortened URLs from history',
                target='urlshortenerclearhistory',
                args_hint=kp.ItemArgsHint.FORBIDDEN,
                hit_hint=kp.ItemHitHint.NOARGS
            ))

        self.set_catalog(catalog)

    def on_suggest(self, user_input, items_chain):
        if not items_chain or items_chain[0].category() != kp.ItemCategory.KEYWORD:
            return

        if items_chain[-1].target() == 'urlshortenerhistory':
            suggestions = self._read_history()
            self.set_suggestions(suggestions, kp.Match.ANY, kp.Sort.NONE)
            return

        if self.should_terminate(0.55) or not user_input:
            return

        if not self._validate_url(user_input):
            self.set_suggestions(
                [
                    self.create_error_item(label='Please, type a valid URL', short_desc='Error')
                ],
                kp.Match.ANY,
                kp.Sort.LABEL_ASC
            )
        else:
            self.set_suggestions(
                [
                    self.create_error_item(label='Shortening link', short_desc='please wait')
                ],
                kp.Match.ANY,
                kp.Sort.LABEL_ASC
            )

            url_shortened = None
            try:
                # Call the service
                url_shortened = self.main_service.shorten(url=user_input)
            except HTTPError as httperror:
                self.err(httperror.read())
                traceback.print_exc()
            except Exception:
                traceback.print_exc()
            finally:
                if url_shortened is None:
                    self.set_suggestions([])
                    self.set_suggestions([
                        self.create_error_item(
                            label='There was an error trying to shorten the URL.',
                            short_desc='Check the console output for more info')
                    ], kp.Match.ANY, kp.Sort.LABEL_ASC)
                else:
                    self.set_suggestions([
                        self.create_item(
                            category=self.ITEM_URL,
                            label=url_shortened,
                            short_desc='Press ENTER to copy',
                            target=url_shortened,
                            args_hint=kp.ItemArgsHint.FORBIDDEN,
                            hit_hint=kp.ItemHitHint.IGNORE
                        )],
                        kp.Match.ANY,
                        kp.Sort.LABEL_ASC
                    )

                    if self.history_enabled:
                        self.historian.add(user_input, url_shortened, self.service_name)

    def on_execute(self, item, action):
        if item.category() not in (self.ITEM_HISTORY, self.ITEM_URL, kp.ItemCategory.KEYWORD):
            return

        if item.target() == 'urlshortenerclearhistory':
            self.historian.clear()
            return

        # Copy the URL from history or copy the shortened url
        if action is None or action.name() == 'copy':
            kpu.set_clipboard(item.label())
            return

        # Open the URL in browser
        if action.name() == 'open':
            kpu.web_browser_command(private_mode=False, url=item.label(), execute=True)
            return

        # Remove the url from history
        if action.name() == 'remove':
            self.historian.remove(item.target())
            return

    def on_events(self, flags):
        if flags & kp.Events.PACKCONFIG:
            self._read_config()
            self.on_catalog()

    # Reads the plugin's configuration
    def _read_config(self):
        settings = self.load_settings()
        self.service_name = settings.get('main_service', section='main', fallback=self.DEFAULT_MAIN_SERVICE)
        if self.service_name not in self.services:
            self.service_name = self.DEFAULT_MAIN_SERVICE

        self.history_enabled = settings.get_bool('enable_history', 'main', fallback='yes')

        api_url = settings.get('API_URL', section=self.service_name)
        api_key = settings.get('API_KEY', section=self.service_name)
        self.main_service = self.services[self.service_name](api_url, api_key)

    # Create the default actions to be used in shortened urls and the entries in history
    def _create_actions(self):
        actions = [
            self.create_action(name="copy", label="Copy URL", short_desc="Copy URL to clipboard"),
            self.create_action(name="remove", label="Remove from history", short_desc="Remove this url from history"),
            self.create_action(name="open", label="Open in browser", short_desc="Open your URL in browser"),
        ]
        self.set_actions(self.ITEM_HISTORY, actions)

    @staticmethod
    # Check if the url is valid
    def _validate_url(url):
        if not url.startswith("http"):
            url = "http://{}".format(url)

        # https://github.com/django/django/blob/stable/1.3.x/django/core/validators.py#L45
        regex = re.compile(
            r'^(?:http)s?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)

        if not regex.search(url):
            return False

        return True

    # Reads the history of shortened URLs and create the suggestions
    def _read_history(self):
        history = self.historian.read()

        suggestions = []
        if history is False:
            suggestions.append(
                self.create_error_item(label='The history file is empty', short_desc='There is no history')
            )
        else:
            for item in history["items"]:
                suggestions.append(
                    self.create_item(
                        category=self.ITEM_HISTORY,
                        label=item['shortUrl'],
                        short_desc="url: {} • service: {}".format(unquote(item['longUrl']), item['service']),
                        target=item['id'],
                        args_hint=kp.ItemArgsHint.FORBIDDEN,
                        hit_hint=kp.ItemHitHint.IGNORE
                    )
                )

        return suggestions
