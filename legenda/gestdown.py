"""Keyless TV subtitle search through Gestdown's public HTTPS API."""
import json
import re
import urllib.error
import urllib.parse
import urllib.request

BASE = 'https://api.gestdown.info'
USER_AGENT = 'LegendasLinux/2.0 (+https://github.com/desenrolado-s/Subtitle-Downloader)'
EPISODE = re.compile(r'(?i)(?:\bs(\d{1,2})e(\d{1,3})\b|\b(\d{1,2})x(\d{1,3})\b)')


def episode_query(title, video=None):
    """Return the show title and episode coordinates inferred from a search or file."""
    text = (video.stem if video else title or '').replace('.', ' ').replace('_', ' ')
    match = EPISODE.search(text)
    if not match:
        return None
    season, episode = match.group(1, 2) if match.group(1) else match.group(3, 4)
    show = text[:match.start()].strip(' -')
    return show, int(season), int(episode)


def _json(path):
    request = urllib.request.Request(BASE + path, headers={'Accept': 'application/json', 'User-Agent': USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            return json.load(response)
    except urllib.error.HTTPError as error:
        if error.code in (404, 423):
            return {}
        raise RuntimeError(f'Gestdown retornou HTTP {error.code}.') from None
    except (urllib.error.URLError, TimeoutError):
        raise RuntimeError('Não foi possível conectar ao Gestdown. Confira a internet e tente novamente.') from None


def _download_url(uri):
    url = urllib.parse.urljoin(BASE, uri)
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme != 'https' or parsed.netloc != 'api.gestdown.info':
        raise ValueError('Link de download do Gestdown inválido.')
    return url


def search(title, video, language):
    """Find matching TV episode subtitles without an API key.

    Gestdown indexes television episodes, so a season and episode marker is
    required.  Use a linked video named like ``Show.S01E02`` for best results.
    """
    query = episode_query(title, video)
    if not query:
        return []
    show_title, season, episode = query
    if len(show_title) < 3:
        return []
    shows = _json('/shows/search/' + urllib.parse.quote(show_title)).get('shows', [])
    if not shows:
        return []
    exact = next((show for show in shows if show.get('name', '').casefold() == show_title.casefold()), shows[0])
    if not exact.get('id'):
        return []
    language_code = language.split('-', 1)[0].lower()
    payload = _json(f"/subtitles/get/{exact['id']}/{season}/{episode}/{urllib.parse.quote(language_code)}")
    rows = []
    for subtitle in payload.get('matchingSubtitles', []):
        if subtitle.get('completed') is False or not subtitle.get('subtitleId') or not subtitle.get('downloadUri'):
            continue
        try:
            download_url = _download_url(subtitle['downloadUri'])
        except ValueError:
            continue
        rows.append((
            {'provider': 'gestdown', 'subtitle_id': subtitle['subtitleId'], 'download_url': download_url},
            {
                'file_name': f"{exact.get('name', show_title)} S{season:02}E{episode:02} {subtitle.get('version', '')}".strip(),
                'language': language,
                'download_count': subtitle.get('downloadCount', 0),
                'source': 'Gestdown (Addic7ed)',
            },
        ))
    return rows


def download(result):
    request = urllib.request.Request(_download_url(result['download_url']), headers={'Accept': 'text/srt, text/plain, */*', 'User-Agent': USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            return response.read(10 * 1024 * 1024 + 1)
    except urllib.error.HTTPError as error:
        raise RuntimeError(f'Gestdown retornou HTTP {error.code} ao baixar a legenda.') from None
    except (urllib.error.URLError, TimeoutError):
        raise RuntimeError('Não foi possível baixar a legenda do Gestdown.') from None
