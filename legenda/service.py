"""GUI-independent subtitle operations."""
import urllib.parse
import urllib.request
from .provider import api
from .files import movie_hash, save_subtitle


def search(title, video, language, key):
    params = {'languages': language, 'order_by': 'download_count', 'order_direction': 'desc'}
    rows = []
    fingerprint = movie_hash(video) if video else None
    if fingerprint:
        rows = api('subtitles?' + urllib.parse.urlencode(dict(params, moviehash=fingerprint, moviehash_match='only')), key).get('data', [])
    if not rows:
        rows = api('subtitles?' + urllib.parse.urlencode(dict(params, query=title or video.stem)), key).get('data', [])
    return [(f, row['attributes']) for row in rows for f in row['attributes'].get('files', [])]


def download(file_id, target, key, user, password):
    token = api('login', key, {'username': user, 'password': password})['token']
    link = api('download', key, {'file_id': file_id, 'sub_format': 'srt'}, token)['link']
    if urllib.parse.urlparse(link).scheme != 'https':
        raise ValueError('Link de download inválido.')
    with urllib.request.urlopen(link, timeout=60) as response:
        content = response.read(10 * 1024 * 1024 + 1)
    return save_subtitle(target, content)
