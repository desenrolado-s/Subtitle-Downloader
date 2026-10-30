#!/usr/bin/env python3
"""Busca gráfica de legendas pelo OpenSubtitles.com (Python 3, Tk)."""
import json
import os
import re
import struct
import tempfile
import threading
import queue
import urllib.request
import urllib.parse
import urllib.error
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

BASE = 'https://api.opensubtitles.com/api/v1/'
BG, FG = '#101112', '#f4f4f0'


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


def api(route, key, payload=None, token=''):
    headers = {'Api-Key': key, 'User-Agent': 'LegendasLinux v1.0', 'Accept': 'application/json'}
    if token:
        headers['Authorization'] = 'Bearer ' + token
    data = None
    if payload is not None:
        data = json.dumps(payload).encode()
        headers['Content-Type'] = 'application/json'
    req = urllib.request.Request(BASE + route, data=data, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        errors = {401: 'Credenciais inválidas.', 403: 'Acesso negado: confira a chave e a conta.', 406: 'Limite de downloads atingido.', 429: 'Muitas requisições. Tente mais tarde.'}
        raise RuntimeError(errors.get(e.code, f'OpenSubtitles retornou HTTP {e.code}.')) from None
    except (urllib.error.URLError, TimeoutError):
        raise RuntimeError('Não foi possível conectar ao OpenSubtitles. Confira a internet e tente novamente.') from None


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


class App:
    def __init__(self, root):
        self.root = root
        root.title('LEGENDA / Linux')
        root.geometry('1100x800')
        root.minsize(900, 740)
        root.configure(bg=BG)
        self.events = queue.Queue()
        self.results = []
        self.busy = False
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('Treeview', background=BG, foreground=FG, fieldbackground=BG, rowheight=42, bordercolor=FG)
        style.configure('Treeview.Heading', background='#222426', foreground=FG, relief='flat')
        style.map('Treeview', background=[('selected', '#495356')])
        main = tk.Frame(root, bg=BG)
        main.pack(fill='both', expand=True, padx=30, pady=24)
        header = tk.Frame(main, bg=BG)
        header.pack(fill='x')
        self.label(header, 'LEGENDA', 24).pack(side='left')
        self.button(header, 'CONTA / CONFIGURAÇÕES', self.settings).pack(side='right')
        self.label(main, 'C I N E M A   /   S E M   B A R R E I R A S', 9).pack(anchor='w', pady=(0, 18))
        tk.Frame(main, bg=FG, height=1).pack(fill='x', pady=(0, 18))
        self.video = tk.StringVar()
        self.query = tk.StringVar()
        self.key = tk.StringVar(value=os.getenv('OPENSUBTITLES_API_KEY', ''))
        self.user = tk.StringVar(value=os.getenv('OPENSUBTITLES_USERNAME', ''))
        self.password = tk.StringVar()
        self.lang = tk.StringVar(value='pt-br')
        self.label(main, 'Encontre a legenda certa.', 28).pack(anchor='w', pady=(6, 6))
        self.label(main, 'Pesquise um filme ou série. O arquivo de vídeo é opcional.', 11).pack(anchor='w', pady=(0, 20))
        self.field(main, '01  /  NOME DO FILME OU SÉRIE', self.query)
        attach = tk.Frame(main, bg=BG)
        attach.pack(fill='x', pady=10)
        self.button(attach, '+ VINCULAR VÍDEO', self.choose).pack(side='left')
        self.button(attach, 'REMOVER', lambda: self.video.set('')).pack(side='left', padx=8)
        self.label(attach, '', 9, textvariable=self.video, wraplength=560).pack(side='left', padx=8)
        row = tk.Frame(main, bg=BG)
        row.pack(fill='x', pady=12)
        self.label(row, 'IDIOMA').pack(side='left', padx=(0, 12))
        self.entry(row, self.lang, width=9).pack(side='left')
        self.label(row, 'pt-br · pt · en · es').pack(side='left', padx=12)
        self.button(row, 'BUSCAR LEGENDAS →', self.search).pack(side='right')
        self.label(main, '02  /  LEGENDAS DISPONÍVEIS').pack(anchor='w', pady=8)
        self.tree = ttk.Treeview(main, columns=('release', 'lang', 'downloads'), show='headings', selectmode='browse')
        for col, title, width in [('release', 'VERSÃO / ARQUIVO', 580), ('lang', 'IDIOMA', 75), ('downloads', 'DOWNLOADS', 100)]:
            self.tree.heading(col, text=title)
            self.tree.column(col, width=width)
        self.tree.pack(fill='both', expand=True)
        self.tree.bind('<Double-1>', lambda event: self.download())
        scrollbar = ttk.Scrollbar(main, orient='horizontal', command=self.tree.xview)
        scrollbar.pack(fill='x')
        self.tree.configure(xscrollcommand=scrollbar.set)
        self.button(main, 'BAIXAR SELECIONADA ↓', self.download).pack(anchor='e', pady=14)
        self.status = tk.StringVar(value='Busque pelo título para começar. Configure sua conta no canto superior direito.')
        self.label(main, '', 10, textvariable=self.status).pack(anchor='w')
        root.after(100, self.poll)

    def settings(self):
        window = tk.Toplevel(self.root)
        window.title('Conta OpenSubtitles')
        window.configure(bg=BG)
        window.geometry('560x420')
        window.transient(self.root)
        body = tk.Frame(window, bg=BG)
        body.pack(fill='both', expand=True, padx=28, pady=24)
        self.label(body, 'Sua conta', 24).pack(anchor='w', pady=(0, 12))
        for title, var, secret in [('CHAVE API', self.key, True), ('USUÁRIO', self.user, False), ('SENHA', self.password, True)]:
            self.field(body, title, var, secret=secret)
        self.label(body, 'Credenciais mantidas apenas nesta sessão.', 9).pack(anchor='w', pady=12)
        self.button(body, 'CONCLUÍDO', window.destroy).pack(anchor='e')
        window.grab_set()

    def label(self, parent, text, size=10, **kw):
        return tk.Label(parent, text=text, bg=BG, fg=FG, font=('DejaVu Sans', size), **kw)

    def entry(self, parent, var, **kw):
        return tk.Entry(parent, textvariable=var, bg=BG, fg=FG, insertbackground=FG, relief='flat', highlightthickness=1, highlightbackground=FG, highlightcolor=FG, font=('DejaVu Sans', 11), **kw)

    def button(self, parent, text, action):
        return tk.Button(parent, text=text, command=action, bg=BG, fg=FG, activebackground=FG, activeforeground=BG, relief='solid', bd=1, padx=16, pady=9, cursor='hand2', font=('DejaVu Sans', 10))

    def field(self, parent, title, var, secret=False, action=None):
        self.label(parent, title).pack(anchor='w', pady=(5, 5))
        row = tk.Frame(parent, bg=BG)
        row.pack(fill='x', pady=(0, 5))
        self.entry(row, var, show='•' if secret else '').pack(side='left', fill='x', expand=True, ipady=7)
        if action:
            self.button(row, *action).pack(side='left', padx=(10, 0))

    def choose(self):
        if self.busy:
            return
        path = filedialog.askopenfilename(title='Selecione o vídeo', filetypes=[('Vídeos', '*.mkv *.mp4 *.avi *.mov *.webm *.m4v'), ('Todos', '*')])
        if path:
            self.video.set(path)
            self.query.set(Path(path).stem.replace('.', ' '))
            self.results = []
            self.tree.delete(*self.tree.get_children())

    def run(self, work, done):
        if self.busy:
            return
        self.busy = True
        self.status.set('Aguarde…')
        def worker():
            try:
                self.events.put((done, work(), None))
            except Exception as e:
                self.events.put((done, None, str(e)))
        threading.Thread(target=worker, daemon=True).start()

    def poll(self):
        try:
            done, result, error = self.events.get_nowait()
            self.busy = False
            if error:
                self.status.set('Não foi possível concluir.')
                messagebox.showerror('LEGENDA', error)
            else:
                done(result)
        except queue.Empty:
            pass
        self.root.after(100, self.poll)

    def search(self):
        if self.busy:
            return
        path, key, lang, query = (Path(self.video.get()) if self.video.get().strip() else None), self.key.get().strip(), self.lang.get().strip(), self.query.get().strip()
        if (path is not None and not path.is_file()) or (path is None and not query) or not key or not re.fullmatch(r'[a-z]{2,3}(?:-[a-z]{2})?', lang):
            messagebox.showinfo('Falta informação', 'Digite o título ou selecione um vídeo válido. Configure a chave API e um idioma (ex.: pt-br).')
            return
        self.results = []
        self.tree.delete(*self.tree.get_children())
        def work():
            h = movie_hash(path) if path else None
            params = {'languages': lang, 'order_by': 'download_count', 'order_direction': 'desc'}
            rows = []
            if h:
                rows = api('subtitles?' + urllib.parse.urlencode(dict(params, moviehash=h, moviehash_match='only')), key).get('data', [])
            if not rows:
                rows = api('subtitles?' + urllib.parse.urlencode(dict(params, query=query or path.stem)), key).get('data', [])
            return [(f, row['attributes']) for row in rows for f in row['attributes'].get('files', [])]
        def done(rows):
            self.results = rows
            self.search_video = path
            self.search_lang = lang
            self.search_title = query
            for i, (f, attr) in enumerate(rows):
                self.tree.insert('', 'end', iid=str(i), values=(f.get('file_name', attr.get('release', '')), attr.get('language'), attr.get('download_count')))
            self.status.set(f'{len(rows)} arquivos encontrados (primeira página). Ajuste o título para refinar.' if rows else 'Nenhuma legenda encontrada. Tente outro título ou idioma.')
        self.run(work, done)

    def download(self):
        if self.busy or not self.tree.selection():
            return
        f, attr = self.results[int(self.tree.selection()[0])]
        if self.search_video:
            target = self.search_video.with_suffix('.' + self.search_lang + '.srt')
        else:
            name = re.sub(r'[^\w .-]', '_', self.search_title).strip(' .') or 'legenda'
            destination = filedialog.asksaveasfilename(title='Salvar legenda', initialfile=f'{name}.{self.search_lang}.srt', defaultextension='.srt', filetypes=[('Legenda SRT', '*.srt')])
            if not destination:
                return
            target = Path(destination)
        if target.exists():
            messagebox.showinfo('Arquivo já existe', f'A legenda já existe: {target}\nRenomeie-a antes de baixar outra versão.')
            return
        key, user, password = self.key.get().strip(), self.user.get().strip(), self.password.get()
        if not user or not password:
            messagebox.showinfo('Conta OpenSubtitles', 'Informe usuário e senha para baixar.')
            return
        def work():
            token = api('login', key, {'username': user, 'password': password})['token']
            data = api('download', key, {'file_id': f['file_id'], 'sub_format': 'srt'}, token)
            link = data['link']
            if urllib.parse.urlparse(link).scheme != 'https':
                raise RuntimeError('O servidor retornou um link inseguro.')
            with urllib.request.urlopen(link, timeout=60) as r:
                content = r.read(10 * 1024 * 1024 + 1)
            return save_subtitle(target, content)
        self.run(work, lambda path: self.status.set(f'Salva: {path}'))


if __name__ == '__main__':
    App(tk.Tk()).root.mainloop()
