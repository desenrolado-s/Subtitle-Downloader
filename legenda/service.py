"""GUI-independent subtitle operations."""
import urllib.parse
import urllib.request
from .provider import api
from .files import movie_hash, save_subtitle
from . import ajatt, gestdown


def search(title, video, language, key):
    results, errors = [], []
    for provider in (gestdown, ajatt):
        try:
            results.extend(provider.search(title, video, language))
        except RuntimeError as error:
            errors.append(error)
    if not key:
        if errors and not results:
            raise errors[0]
        return results
    params = {'languages': language, 'order_by': 'download_count', 'order_direction': 'desc'}
    rows = []
    fingerprint = movie_hash(video) if video else None
    if fingerprint:
        rows = api('subtitles?' + urllib.parse.urlencode(dict(params, moviehash=fingerprint, moviehash_match='only')), key).get('data', [])
    if not rows:
        rows = api('subtitles?' + urllib.parse.urlencode(dict(params, query=title or video.stem)), key).get('data', [])
    results.extend((dict(file, provider='opensubtitles'), dict(row['attributes'], source='OpenSubtitles')) for row in rows for file in row['attributes'].get('files', []))
    return results


def download(result, target, key='', user='', password=''):
    if result.get('provider') == 'gestdown':
        return save_subtitle(target, gestdown.download(result))
    if result.get('provider') == 'ajatt':
        return save_subtitle(target, ajatt.download(result))
    file_id = result['file_id']
    token = api('login', key, {'username': user, 'password': password})['token']
    link = api('download', key, {'file_id': file_id, 'sub_format': 'srt'}, token)['link']
    if urllib.parse.urlparse(link).scheme != 'https':
        raise ValueError('Link de download inválido.')
    with urllib.request.urlopen(link, timeout=60) as response:
        content = response.read(10 * 1024 * 1024 + 1)
    return save_subtitle(target, content)
