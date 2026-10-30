"""Video identification and atomic subtitle storage."""
import os
import re
import struct
import tempfile
from pathlib import Path

def movie_hash(path):
    size = path.stat().st_size
    if size < 131072:
        return None
    total = size
    with path.open('rb') as f:
        for offset in (0, size - 65536):
            f.seek(offset)
            total += sum(struct.unpack('<8192Q', f.read(65536)))
    return f'{total & 0xffffffffffffffff:016x}'


def save_subtitle(target, content):
    """Publica somente arquivos completos, sem substituir arquivos existentes."""
    if len(content) > 10 * 1024 * 1024 or not re.search(
        rb'\d{2}:\d{2}:\d{2}[,.]\d{3}\s*-->\s*\d{2}:\d{2}:\d{2}[,.]\d{3}', content
    ):
        raise RuntimeError('Resposta não parece uma legenda SRT válida.')
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=target.parent, prefix='.legenda-', delete=False) as out:
            temporary = Path(out.name)
            out.write(content)
            out.flush()
            os.fsync(out.fileno())
        os.link(temporary, target)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    return target


