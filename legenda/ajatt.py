"""Japanese anime subtitle search through AJATT's public catalog."""
from html.parser import HTMLParser
import re
import urllib.error
import urllib.parse
import urllib.request

CATALOG = 'https://subtitles.ajatt.top/'
ALLOWED_HOSTS = {'subtitles.ajatt.top', 'raw.githubusercontent.com'}
USER_AGENT = 'LegendasLinux/2.0 (+https://github.com/desenrolado-s/Subtitle-Downloader)'
MAX_RESPONSE = 5 * 1024 * 1024
EPISODE = re.compile(r'(?i)\b(?:s\d{1,2}e\d{1,3}|\d{1,2}x\d{1,3})\b')


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self._href = None
        self._text = []

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            self._href = dict(attrs).get('href')
            self._text = []

    def handle_data(self, data):
        if self._href is not None:
            self._text.append(data)

    def handle_endtag(self, tag):
        if tag == 'a' and self._href is not None:
            self.links.append((self._href, ''.join(self._text).strip()))
            self._href = None
            self._text = []


def _url(url, base=CATALOG):
    resolved = urllib.parse.urljoin(base, url)
    parsed = urllib.parse.urlparse(resolved)
    if parsed.scheme != 'https' or parsed.netloc not in ALLOWED_HOSTS:
        raise ValueError('Link de download do AJATT inválido.')
    if parsed.netloc == 'raw.githubusercontent.com' and not parsed.path.startswith('/Ajatt-Tools/kitsunekko-mirror/main/subtitles/'):
        raise ValueError('Link de download do AJATT inválido.')
    return resolved


def _links(url):
    request = urllib.request.Request(_url(url), headers={'Accept': 'text/html', 'User-Agent': USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            body = response.read(MAX_RESPONSE + 1)
    except urllib.error.HTTPError as error:
        raise RuntimeError(f'AJATT retornou HTTP {error.code}.') from None
    except (urllib.error.URLError, TimeoutError):
        raise RuntimeError('Não foi possível conectar ao catálogo AJATT.') from None
    if len(body) > MAX_RESPONSE:
        raise RuntimeError('Catálogo AJATT grande demais para consultar com segurança.')
    parser = Links()
    parser.feed(body.decode('utf-8', errors='replace'))
    return parser.links


def _terms(title):
    clean = EPISODE.sub(' ', title).casefold()
    return tuple(part for part in re.split(r'[^\w]+', clean) if len(part) > 1)


def search(title, video, language):
    """Return Japanese SRT subtitles for anime, without credentials."""
    if language.split('-', 1)[0].lower() not in ('ja', 'jpn'):
        return []
    query = _terms(title or (video.stem if video else ''))
    if not query:
        return []
    candidates = []
    for href, name in _links(CATALOG):
        if href.endswith('.html') and all(term in name.casefold() for term in query):
            candidates.append((href, name))
    if not candidates:
        return []
    href, name = next((item for item in candidates if _terms(item[1]) == query), candidates[0])
    rows = []
    page_url = _url(href)
    for file_href, file_name in _links(page_url):
        if not file_href.casefold().endswith('.srt'):
            continue
        try:
            download_url = _url(file_href, page_url)
        except ValueError:
            continue
        rows.append((
            {'provider': 'ajatt', 'download_url': download_url},
            {'file_name': file_name or urllib.parse.unquote(urllib.parse.urlparse(download_url).path.rsplit('/', 1)[-1]), 'language': 'ja', 'download_count': 0, 'source': 'AJATT / Kitsunekko'},
        ))
    return rows


def download(result):
    request = urllib.request.Request(_url(result['download_url']), headers={'Accept': 'text/srt, text/plain, */*', 'User-Agent': USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            return response.read(10 * 1024 * 1024 + 1)
    except urllib.error.HTTPError as error:
        raise RuntimeError(f'AJATT retornou HTTP {error.code} ao baixar a legenda.') from None
    except (urllib.error.URLError, TimeoutError):
        raise RuntimeError('Não foi possível baixar a legenda do AJATT.') from None
