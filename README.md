<div align="center">

<h1>LEGENDA</h1>

<p><strong>Baixe legendas do OpenSubtitles e de fontes públicas em uma interface GTK 4 nativa, rápida e sem distrações.</strong></p>

<p>
  <a href="https://github.com/desenrolado-s/Subtitle-Downloader/actions/workflows/gtk.yml"><img src="https://github.com/desenrolado-s/Subtitle-Downloader/actions/workflows/gtk.yml/badge.svg" alt="GTK migration validation"></a>
  <a href="https://github.com/desenrolado-s/Subtitle-Downloader/releases/latest"><img src="https://img.shields.io/github/v/release/desenrolado-s/Subtitle-Downloader?label=release" alt="Última release"></a>
  <a href="https://www.python.org/"><img src="https://img.shields.io/badge/python-3.12%2B-3776AB?logo=python&logoColor=white" alt="Python 3.12+"></a>
  <a href="https://www.gtk.org/"><img src="https://img.shields.io/badge/GTK-4-4A86CF?logo=gtk&logoColor=white" alt="GTK 4"></a>
  <a href="#requisitos"><img src="https://img.shields.io/badge/platform-Linux-FCC624?logo=linux&logoColor=black" alt="Linux"></a>
</p>

</div>

## Visão geral

LEGENDA é um aplicativo desktop para Linux que pesquisa e baixa legendas do OpenSubtitles e de fontes públicas. A interface usa GTK 4 e executa as operações de rede em segundo plano, mantendo a janela responsiva.

O vídeo nunca é enviado ao serviço. A busca usa o hash do arquivo quando ele está vinculado e, se necessário, recorre ao título.

## Recursos

- Busca por título ou por hash do vídeo.
- Vínculo opcional de um arquivo de vídeo local.
- Filtro por idioma, como `pt-br`, `pt`, `en` e `es`.
- Download em SRT com validação de conteúdo e gravação atômica.
- Credenciais guardadas no cofre Secret Service do sistema.
- Interface escura, minimalista e nativa em GTK 4.

## Requisitos

- Linux com X11 ou Wayland.
- Python 3.12 ou superior.
- GTK 4 e PyGObject.
- `keyring` e um serviço Secret Service ativo, como GNOME Keyring ou KWallet, para salvar credenciais.
- Conta e chave de API do OpenSubtitles, apenas para o catálogo OpenSubtitles.

## Instalação

Clone o repositório e execute o aplicativo:

```sh
git clone https://github.com/desenrolado-s/Subtitle-Downloader.git
cd Subtitle-Downloader
python3 app.py
```

Instale as dependências do sistema conforme a sua distribuição:

| Distribuição | Comando |
| --- | --- |
| Arch Linux | `sudo pacman -S python-gobject gtk4 python-keyring` |
| Ubuntu / Debian | `sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-4.0 python3-keyring` |
| Fedora | `sudo dnf install python3-gobject gtk4 python3-keyring` |

As bibliotecas GTK precisam vir do sistema. Em um ambiente virtual, use `--system-site-packages` para que o Python consiga importar o PyGObject.

## Atualizações do AppImage

Cada release publica um arquivo `.zsync` estável em:

```text
https://github.com/desenrolado-s/Subtitle-Downloader/releases/latest/download/Legenda-linux-x64.AppImage.zsync
```

O AppImage tem essa informação de atualização embutida, então é possível baixar apenas os blocos que mudaram com o `AppImageUpdate` ou o `appimageupdatetool` do projeto [AppImageUpdate](https://github.com/AppImageCommunity/AppImageUpdate/releases):

```sh
chmod +x appimageupdatetool-*.AppImage
./appimageupdatetool-*.AppImage ./Legenda-linux-x64*.AppImage
```

Também é possível abrir o AppImage baixado na interface gráfica do `AppImageUpdate`.

## Configuração da conta

1. Crie uma conta em [opensubtitles.com](https://www.opensubtitles.com).
2. Gere uma chave de aplicação em [opensubtitles.com/consumers](https://www.opensubtitles.com/consumers).
3. Abra **Conta** na barra superior e informe chave, usuário e senha.
4. Se quiser manter os dados entre sessões, use **Salvar no cofre**.

A chave e o usuário também podem ser definidos pelas variáveis de ambiente `OPENSUBTITLES_API_KEY` e `OPENSUBTITLES_USERNAME`. A senha é solicitada apenas na interface e nunca é gravada em texto puro. Sem um cofre disponível, as credenciais valem somente para a sessão atual.

## Fontes sem chave de API

Para episódios de séries, o app também consulta o **Gestdown**, uma API pública que fornece legendas do catálogo Addic7ed por HTTPS, sem chave ou conta. Vincule um vídeo cujo nome contenha o episódio, por exemplo `Minha.Serie.S01E02.mkv`, ou pesquise por `Minha Série S01E02`. Os resultados indicam a fonte e podem ser baixados sem preencher **Conta**.

O Gestdown é voltado para episódios de TV e a disponibilidade varia por idioma e release. Para filmes ou buscas somente por título, configure a conta OpenSubtitles para acessar seu catálogo.

## Como usar

1. Digite o nome do filme ou da série. Vincular um vídeo é opcional.
2. Ajuste o idioma se necessário.
3. Clique em **Buscar legendas** e selecione uma versão na lista.
4. Clique em **Baixar selecionada**.

Com um vídeo vinculado, a legenda é salva ao lado dele no formato `filme.pt-br.srt`, reconhecido por players como VLC e mpv. Sem vídeo, o aplicativo abre o diálogo **Salvar como**.

## Como a busca funciona

1. Se houver um vídeo vinculado com pelo menos 128 KiB, o aplicativo calcula o hash e procura uma correspondência exata.
2. Se o hash não retornar resultados, a busca é feita pelo título.
3. A lista mostra a primeira página de resultados, ordenada por número de downloads. Refine o título quando necessário.

Downloads do OpenSubtitles exigem usuário e senha. Os resultados do Gestdown não exigem credenciais. O aplicativo recusa links que não usam HTTPS, valida o conteúdo como SRT e não sobrescreve legendas existentes.

A disponibilidade, a sincronização e os limites diários dependem do catálogo e do plano da conta no OpenSubtitles. Nenhum catálogo contém legendas para todos os vídeos.

## Estrutura do projeto

| Caminho | Responsabilidade |
| --- | --- |
| `app.py` | Ponto de entrada GTK e tratamento do modo `--smoke-test`. |
| `legenda/ui.py` | Janela GTK 4, diálogo de conta e coordenação das tarefas em segundo plano. |
| `legenda/service.py` | Busca e download independentes da interface. |
| `legenda/provider.py` | Cliente REST do OpenSubtitles e mensagens de erro. |
| `legenda/gestdown.py` | Fonte pública Gestdown/Addic7ed para episódios de TV, sem chave de API. |
| `legenda/files.py` | Hash do vídeo, validação do SRT e gravação atômica. |
| `legenda/credentials.py` | Leitura e gravação das credenciais no Secret Service. |
| `test_*.py` | Testes de arquivos, API, serviço, credenciais e interface GTK. |
| `packaging/linux/` | Arquivo `.desktop` e ícones do aplicativo. |
| `scripts/build-appimage.sh` | Empacotamento do AppImage. |
| `.github/workflows/build.yml` | Testes, builds de Linux/macOS e publicação de releases. |
| `.github/workflows/gtk.yml` | Validação da interface GTK e do AppImage no GitHub Actions. |

## Testes

Execute a suíte completa:

```sh
python3 -m unittest discover -v
```

Os testes da interface GTK são ignorados quando não há display. Para executá-los em um ambiente headless:

```sh
dbus-run-session -- xvfb-run -a python3 -m unittest discover -v
```

## Build e empacotamento

Para gerar um executável local com PyInstaller:

```sh
python3 -m venv --system-site-packages .venv
.venv/bin/python -m pip install -r requirements-build.txt
.venv/bin/python -m unittest discover -v
.venv/bin/python -m PyInstaller --noconfirm --clean --onedir --windowed --name Legenda \
  --hidden-import=keyring.backends.SecretService \
  --hidden-import=gi.repository.Gtk \
  --hidden-import=gi.repository.Gdk \
  --hidden-import=gi.repository.Gio \
  --hidden-import=gi.repository.GLib app.py
```

O resultado fica em `dist/Legenda`. Para gerar o AppImage no Ubuntu 22.04:

```sh
bash scripts/build-appimage.sh
```

O script produz `Legenda-linux-x64.AppImage` e baixa a versão `continuous` do `appimagetool`, que não é fixada por hash. O workflow `gtk.yml` executa os testes, empacota o aplicativo, testa o binário e publica o artefato `Legenda-GTK-linux-x64.AppImage`.

O workflow `build.yml` executa os testes e empacota Linux x64 e macOS ARM64. Tags `v*` publicam os pacotes em uma GitHub Release.

Os nomes dos arquivos publicados incluem a tag da release, por exemplo `Legenda-linux-x64-v2.0.3.AppImage`. O link direto da release mais recente também usa esse nome:

```text
https://github.com/desenrolado-s/Subtitle-Downloader/releases/latest/download/Legenda-linux-x64-v2.0.3.AppImage
```

Substitua `v2.0.3` pela tag exibida na release desejada.

## Estado atual e limitações

- A interface GTK é a versão atual. O empacotamento oficial cobre Linux x64 e macOS ARM64; Windows não é suportado no momento.
- A release `v1.0.1` corresponde à versão anterior com Tkinter. Novas tags usam o empacotamento GTK.
- O AppImage é x86_64, usa como base Ubuntu 22.04/glibc 2.35 e não tem compatibilidade garantida com distribuições anteriores, Alpine/musl ou Linux ARM.
- Os pacotes não são assinados nem notarizados.
- O download real depende de credenciais válidas e dos limites da conta OpenSubtitles.
