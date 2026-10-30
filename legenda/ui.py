"""GTK 4 desktop interface."""
import os
import re
import threading
from pathlib import Path
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, Gdk, GLib
from . import service, credentials

CSS = '''
window { background: #111315; color: #f4f4f0; }
headerbar { background: #111315; box-shadow: none; border-bottom: 1px solid #777; }
button, entry { border-radius: 0; border: 1px solid #aaa; padding: 10px 14px; background: transparent; color: #f4f4f0; }
button:hover { background: #34383c; }
button.primary { background: #eee; color: #111; }
.title { font-size: 32px; font-weight: bold; }
.muted { color: #a7adb2; }
list { background: transparent; }
row { padding: 16px; border-bottom: 1px solid #444; }
row:selected { background: #353b41; }
scrolledwindow overshoot.top { background-image: radial-gradient(ellipse at center top, alpha(#f4f4f0, 0.22), transparent); }
scrolledwindow overshoot.bottom { background-image: radial-gradient(ellipse at center bottom, alpha(#f4f4f0, 0.22), transparent); }
'''

def _load_css(provider, css_data):
    text = css_data.decode('utf-8') if isinstance(css_data, bytes) else css_data
    if hasattr(provider, 'load_from_string'):
        provider.load_from_string(text)
        return
    for args in [(text,), (text.encode('utf-8'),), (text, len(text.encode('utf-8'))), (text.encode('utf-8'), len(text.encode('utf-8')))]:
        try:
            provider.load_from_data(*args)
            return
        except (TypeError, ValueError):
            continue

class App(Gtk.Application):
    def __init__(self, smoke=False):
        super().__init__(application_id='io.github.desenrolado_s.Legenda')
        self.smoke = smoke
        self.video = None
        self.results = []
        self.busy = False
        if self.smoke:
            GLib.timeout_add(3000, lambda: (self.quit(), False)[1])

    def do_activate(self):
        if getattr(self, 'window', None):
            self.window.present()
            return
        self.window = Gtk.ApplicationWindow(application=self, title='LEGENDA')
        self.window.set_default_size(1000, 760)
        css = Gtk.CssProvider()
        _load_css(css, CSS)
        Gtk.StyleContext.add_provider_for_display(Gdk.Display.get_default(), css, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        header = Gtk.HeaderBar()
        header.pack_end(self.button('Conta', self.settings))
        self.window.set_titlebar(header)
        self.body = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=18)
        for side in ('top', 'bottom', 'start', 'end'):
            getattr(self.body, 'set_margin_' + side)(28)
        self.window.set_child(self.body)
        self.body.append(self.label('Encontre a legenda certa.', 'title'))
        self.body.append(self.label('Busque pelo título. Vincule um vídeo para encontrar a versão exata.', 'muted'))
        self.query = Gtk.Entry(placeholder_text='Nome do filme ou série')
        self.query.connect('activate', lambda _: self.search())
        self.body.append(self.query)
        bar = Gtk.Box(spacing=12)
        self.language = Gtk.Entry(text='pt-br', width_chars=7)
        bar.append(self.language)
        bar.append(self.button('+ Vincular vídeo', self.choose_video))
        bar.append(self.button('Remover vídeo', self.clear_video))
        search = self.button('Buscar legendas →', self.search)
        search.add_css_class('primary')
        bar.append(search)
        self.body.append(bar)
        self.video_label = self.label('Nenhum vídeo vinculado', 'muted')
        self.body.append(self.video_label)
        self.list = Gtk.ListBox(selection_mode=Gtk.SelectionMode.SINGLE)
        self.list.set_cursor_from_name('pointer')
        scroll = Gtk.ScrolledWindow(vexpand=True)
        scroll.set_kinetic_scrolling(True)
        scroll.set_overlay_scrolling(True)
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll.set_child(self.list)
        self.body.append(scroll)
        self.body.append(self.button('Baixar selecionada ↓', self.download))
        self.status = self.label('Digite um título para começar.', 'muted')
        self.body.append(self.status)
        self.key = Gtk.Entry(text=os.getenv('OPENSUBTITLES_API_KEY', ''), visibility=False)
        self.user = Gtk.Entry(text=os.getenv('OPENSUBTITLES_USERNAME', ''))
        self.password = Gtk.Entry(visibility=False)
        if not self.smoke:
            try:
                saved = credentials.load()
                if saved:
                    self.key.set_text(saved['key'])
                    self.user.set_text(saved['user'])
                    self.password.set_text(saved['password'])
            except Exception:
                self.status.set_text('Cofre indisponível. Você pode informar as credenciais em Conta.')
        self.window.present()
        if self.smoke:
            GLib.timeout_add(300, lambda: (self.quit(), False)[1])

    def label(self, text, style=''):
        label = Gtk.Label(label=text, xalign=0, wrap=True)
        if style:
            label.add_css_class(style)
        return label

    def button(self, text, callback):
        button = Gtk.Button(label=text)
        button.set_cursor_from_name('pointer')
        button.connect('clicked', lambda _: callback())
        return button

    def settings(self):
        if getattr(self, 'account', None):
            self.account.present()
            return
        self.account = Gtk.Window(title='Conta OpenSubtitles', transient_for=self.window, modal=True)
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        for side in ('top', 'bottom', 'start', 'end'):
            getattr(box, 'set_margin_' + side)(24)
        for title, widget in [('Chave API', self.key), ('Usuário', self.user), ('Senha', self.password)]:
            box.append(self.label(title))
            box.append(widget)
        self.account_status = self.label('Salve para lembrar a conta na próxima abertura.', 'muted')
        box.append(self.account_status)
        box.append(self.button('Salvar no cofre', self.save_credentials))
        box.append(self.button('Esquecer credenciais salvas', self.forget_credentials))
        box.append(self.button('Concluído', self.account.hide))
        self.account.set_child(box)
        self.account.connect('close-request', lambda w: (w.hide(), True)[1])
        self.account.present()

    def save_credentials(self):
        values = (self.key.get_text().strip(), self.user.get_text().strip(), self.password.get_text())
        if not all(values):
            self.account_status.set_text('Preencha chave API, usuário e senha.')
            return
        try:
            credentials.save(*values)
        except Exception:
            self.account_status.set_text('Não foi possível salvar. Desbloqueie o cofre Secret Service do sistema e tente novamente.')
        else:
            self.account_status.set_text('Credenciais salvas no cofre do sistema.')

    def forget_credentials(self):
        try:
            credentials.forget()
        except Exception:
            self.account_status.set_text('Não foi possível remover as credenciais. Confira o cofre do sistema.')
        else:
            for widget in (self.key, self.user, self.password):
                widget.set_text('')
            self.account_status.set_text('Credenciais removidas do cofre e desta sessão.')

    def chooser(self, save, callback):
        self.dialog = Gtk.FileChooserNative(title='Salvar legenda' if save else 'Selecionar vídeo', transient_for=self.window, action=Gtk.FileChooserAction.SAVE if save else Gtk.FileChooserAction.OPEN)
        if save:
            self.dialog.set_current_name('legenda.' + self.search_language + '.srt')
        def response(dialog, result):
            file = dialog.get_file()
            dialog.destroy()
            if result == Gtk.ResponseType.ACCEPT and file and file.get_path():
                callback(Path(file.get_path()))
        self.dialog.connect('response', response)
        self.dialog.show()

    def choose_video(self):
        if not self.busy:
            self.chooser(False, self.set_video)

    def set_video(self, path):
        self.video = path
        self.video_label.set_text(str(path))
        self.query.set_text(path.stem.replace('.', ' '))

    def clear_video(self):
        if not self.busy:
            self.video = None
            self.video_label.set_text('Nenhum vídeo vinculado')

    def run_task(self, work, done):
        if self.busy:
            return
        self.busy = True
        self.status.set_text('Aguarde…')
        def finish(value, error):
            self.busy = False
            if error:
                self.status.set_text(str(error))
            else:
                done(value)
            return False
        def worker():
            try:
                value = work()
            except Exception as error:
                GLib.idle_add(finish, None, error)
            else:
                GLib.idle_add(finish, value, None)
        threading.Thread(target=worker, daemon=True).start()

    def search(self):
        if self.busy:
            return
        title, lang, key = self.query.get_text().strip(), self.language.get_text().strip(), self.key.get_text().strip()
        if not (title or self.video) or not key or not re.fullmatch(r'[a-z]{2,3}(?:-[a-z]{2})?', lang):
            self.status.set_text('Informe título ou vídeo, idioma e chave API em Conta.')
            return
        video = self.video
        self.results = []
        while self.list.get_first_child():
            self.list.remove(self.list.get_first_child())
        def done(rows):
            self.results = rows
            self.search_video, self.search_language = video, lang
            for file, attrs in rows:
                self.list.append(self.label(f"{file.get('file_name', 'Legenda')}\n{attrs.get('language', '')} · {attrs.get('download_count', 0)} downloads"))
            self.status.set_text(f'{len(rows)} arquivos encontrados. Selecione uma versão.' if rows else 'Nenhum resultado. Tente outro título ou idioma.')
        self.run_task(lambda: service.search(title, video, lang, key), done)

    def download(self):
        row = self.list.get_selected_row()
        if self.busy or row is None:
            return
        file, _ = self.results[row.get_index()]
        key, user, password = self.key.get_text(), self.user.get_text(), self.password.get_text()
        if not all((key, user, password)):
            self.status.set_text('Preencha chave, usuário e senha em Conta.')
            return
        def save(path):
            if path.exists():
                self.status.set_text('O arquivo já existe. Escolha outro nome.')
                return
            self.run_task(lambda: service.download(file['file_id'], path, key, user, password), lambda p: self.status.set_text(f'Salva: {p}'))
        if self.search_video:
            save(self.search_video.with_suffix('.' + self.search_language + '.srt'))
        else:
            self.chooser(True, save)
