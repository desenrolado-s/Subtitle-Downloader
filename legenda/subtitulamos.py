"""Keyless TV subtitle search through Subtitulamos.tv's public HTTPS site."""
from html.parser import HTMLParser
import json
import re
import urllib.error
import urllib.parse
import urllib.request

BASE = 'https://www.subtitulamos.tv/'
ALLOWED_HOSTS = {'www.subtitulamos.tv', 'subtitulamos.tv'}
USER_AGENT = 'LegendasLinux/2.0 (+https://github.com/desenrolado-s/Subtitle-Downloader)'
EPISODE = re.compile(r'(?i)(?:\bs(\d{1,2})e(\d{1,3})\b|\b(\d{1,2})x(\d{1,3})\b)')
LANGUAGES = {
    'en': {'english', 'english (us)', 'english (uk)'},
    'pt': {'portuguese', 'brazilian'},
}


class _EpisodePage(HTMLParser):
    def __init__(self):
        super().__init__()
        self.items = []
        self.language = None
        self._language_depth = 0
        self._text = []
        self._progress_depth = 0
        self._href = None

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        if tag == 'div':
            if self._language_depth:
                self._language_depth += 1
            elif 'subtitle_language' in attributes.get('class', '').split():
                self._language_depth, self._text = 1, []
            if self._progress_depth:
                self._progress_depth += 1
            elif attributes.get('id') == 'progress_buttons_row':
                self._progress_depth, self._href = 1, None
        elif tag == 'a' and self._progress_depth and not self._href:
            self._href = attributes.get('href')

    def handle_data(self, data):
        if self._language_depth:
            self._text.append(data)

    def handle_endtag(self, tag):
        if tag != 'div':
            return
        if self._language_depth:
            self._language_depth -= 1
            if not self._language_depth:
                self.language = ''.join(self._text).strip().casefold()
        if self._progress_depth:
            self._progress_depth -= 1
            if not self._progress_depth and self._href:
                self.items.append((self.language, self._href))


def _url(url, base=BASE):
    resolved = urllib.parse.urljoin(base, url)
    parsed = urllib.parse.urlparse(resolved)
    if parsed.scheme != 'https' or parsed.netloc not in ALLOWED_HOSTS:
        raise ValueError('Link de download do Subtitulamos inválido.')
    return resolved


def _request(url, accept):
    request = urllib.request.Request(_url(url), headers={'Accept': accept, 'Referer': BASE, 'User-Agent': USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return response.read(5 * 1024 * 1024 + 1)
    except urllib.error.HTTPError as error:
        raise RuntimeError(f'Subtitulamos retornou HTTP {error.code}.') from None
    except (urllib.error.URLError, TimeoutError):
        raise RuntimeError('Não foi possível conectar ao Subtitulamos.') from None


def _episode(title, video):
    text = (video.stem if video else title or '').replace('.', ' ').replace('_', ' ')
    match = EPISODE.search(text)
    if not match:
        return None
    season, episode = match.group(1, 2) if match.group(1) else match.group(3, 4)
    return text[:match.start()].strip(' -'), int(season), int(episode)


def _search(title, season, episode):
    query = f'{title} {season}x{episode}'
    body = _request('search/query?' + urllib.parse.urlencode({'q': query}), 'application/json')
    if len(body) > 5 * 1024 * 1024:
        raise RuntimeError('Resposta do Subtitulamos grande demais para consultar com segurança.')
    try:
        return json.loads(body.decode('utf-8'))
    except (ValueError, UnicodeDecodeError):
        raise RuntimeError('Resposta inválida do Subtitulamos.') from None


def _episode_url(title, season, episode):
    normalized = title.casefold()
    for show in _search(title, season, episode):
        if normalized not in str(show.get('name', '')).casefold():
            continue
        for item in show.get('episodes', []):
            if item.get('season') == season and item.get('number') == episode and item.get('id'):
                return _url('episodes/' + str(item['id']))
    return None


def _subtitle_rows(page, language):
    parser = _EpisodePage()
    parser.feed(page.decode('utf-8', errors='replace'))
    wanted = LANGUAGES.get(language.split('-', 1)[0].lower(), set())
    rows = []
    for current_language, href in parser.items:
        if current_language not in wanted:
            continue
        try:
            download_url = _url(href)
        except ValueError:
            continue
        rows.append(({'provider': 'subtitulamos', 'download_url': download_url}, {
            'file_name': urllib.parse.unquote(urllib.parse.urlparse(download_url).path.rsplit('/', 1)[-1]) or 'Legenda',
            'language': language,
            'download_count': 0,
            'source': 'Subtitulamos.tv',
        }))
    return rows


def search(title, video, language):
    """Find English or Portuguese TV episode subtitles without credentials."""
    if language.split('-', 1)[0].lower() not in LANGUAGES:
        return []
    query = _episode(title, video)
    if not query or len(query[0]) < 3:
        return []
    url = _episode_url(*query)
    if not url:
        return []
    return _subtitle_rows(_request(url, 'text/html'), language)


def download(result):
    return _request(result['download_url'], 'text/srt, text/plain, */*')
