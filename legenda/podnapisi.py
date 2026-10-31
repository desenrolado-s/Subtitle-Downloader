"""Keyless multilingual subtitle search through Podnapisi's public XML API."""
import io
import re
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
import zipfile

BASE = 'https://www.podnapisi.net'
USER_AGENT = 'LegendasLinux/2.0 (+https://github.com/desenrolado-s/Subtitle-Downloader)'
MAX_RESPONSE = 5 * 1024 * 1024
MAX_SUBTITLE = 10 * 1024 * 1024
LANGUAGES = {'en': 2, 'pt': 26, 'ja': 11, 'es': 28, 'fr': 8, 'de': 14, 'it': 9, 'ko': 4, 'ru': 27, 'zh': 17}
EPISODE = re.compile(r'(?i)(?:\bs(\d{1,2})e(\d{1,3})\b|\b(\d{1,2})x(\d{1,3})\b)')


def _url(path):
    url = urllib.parse.urljoin(BASE + '/', path)
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme != 'https' or parsed.netloc != 'www.podnapisi.net':
        raise ValueError('Link de download do Podnapisi inválido.')
    return url


def _fetch(url, accept):
    request = urllib.request.Request(_url(url), headers={'Accept': accept, 'User-Agent': USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return response.read(MAX_RESPONSE + 1)
    except urllib.error.HTTPError as error:
        raise RuntimeError(f'Podnapisi retornou HTTP {error.code}.') from None
    except (urllib.error.URLError, TimeoutError):
        raise RuntimeError('Não foi possível conectar ao Podnapisi.') from None


def _coordinates(title, video):
    text = (video.stem if video else title or '').replace('.', ' ').replace('_', ' ')
    match = EPISODE.search(text)
    if not match:
        return text.strip(), None, None
    season, episode = match.group(1, 2) if match.group(1) else match.group(3, 4)
    return text[:match.start()].strip(' -'), int(season), int(episode)


def _xml(body):
    if len(body) > MAX_RESPONSE:
        raise RuntimeError('Resposta do Podnapisi grande demais para consultar com segurança.')
    # Do not permit a third-party response to define entities or pull external data.
    if b'<!DOCTYPE' in body.upper() or b'<!ENTITY' in body.upper():
        raise RuntimeError('Resposta XML inválida do Podnapisi.')
    try:
        return ET.fromstring(body)
    except ET.ParseError:
        raise RuntimeError('Resposta XML inválida do Podnapisi.') from None


def _text(node, tag, default=''):
    child = node.find(tag)
    return child.text.strip() if child is not None and child.text else default


def search(title, video, language):
    """Find movie or episode subtitles in several languages without credentials."""
    language_code = language.split('-', 1)[0].lower()
    if language_code not in LANGUAGES:
        return []
    query, season, episode = _coordinates(title, video)
    if len(query) < 2:
        return []
    params = {'sXML': 1, 'sK': query, 'sL': LANGUAGES[language_code]}
    if season is not None:
        params['sTS'] = season
        params['sTE'] = episode
    root = _xml(_fetch('subtitles/search/old?' + urllib.parse.urlencode(params), 'application/xml, text/xml'))
    rows = []
    for subtitle in root.findall('.//subtitle'):
        identifier = _text(subtitle, 'pid') or _text(subtitle, 'id')
        if not identifier or not identifier.isdigit():
            continue
        subtitle_language = _text(subtitle, 'language').lower()
        if subtitle_language and subtitle_language not in (str(LANGUAGES[language_code]), language_code):
            continue
        release = _text(subtitle, 'release') or _text(subtitle, 'title') or f'{identifier}.srt'
        try:
            count = int(_text(subtitle, 'downloads', '0'))
        except ValueError:
            count = 0
        rows.append((
            {'provider': 'podnapisi', 'subtitle_id': identifier, 'download_url': _url(f'subtitles/{identifier}/download')},
            {'file_name': release, 'language': language, 'download_count': count, 'source': 'Podnapisi'},
        ))
    return rows


def _srt_from_archive(content):
    try:
        with zipfile.ZipFile(io.BytesIO(content)) as archive:
            choices = [item for item in archive.infolist() if not item.is_dir() and item.filename.casefold().endswith('.srt')]
            if len(choices) != 1 or choices[0].file_size > MAX_SUBTITLE:
                raise RuntimeError('Arquivo do Podnapisi não contém uma legenda SRT segura.')
            with archive.open(choices[0]) as subtitle:
                body = subtitle.read(MAX_SUBTITLE + 1)
    except zipfile.BadZipFile:
        raise RuntimeError('Arquivo inválido recebido do Podnapisi.') from None
    if len(body) > MAX_SUBTITLE:
        raise RuntimeError('Legenda do Podnapisi grande demais.')
    return body


def download(result):
    content = _fetch(result['download_url'], 'application/zip, text/srt, text/plain, */*')
    if content.startswith(b'PK\x03\x04'):
        return _srt_from_archive(content)
    if len(content) > MAX_SUBTITLE:
        raise RuntimeError('Legenda do Podnapisi grande demais.')
    return content
