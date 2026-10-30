# Branch experimental GTK 4

Esta branch `feature/gtk4-ui` migra a interface para GTK 4. A versão Tkinter permanece na branch `main`. Para executar: `python3 app.py`.

Dependências de execução:
- Arch: `sudo pacman -S python-gobject gtk4`
- Ubuntu/Debian: `sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-4.0`
- Fedora: `sudo dnf install python3-gobject gtk4`

`legenda/ui.py` contém a interface GTK; `legenda/service.py` concentra busca/download sem depender de widgets. A interface Tkinter foi removida desta branch; seu histórico permanece em `main`. Não há fallback silencioso para Tkinter.

Estado: testes unitários dos arquivos, API e serviço, mais testes gráficos GTK executados no CI. O workflow `gtk.yml` prepara um AppImage GTK em Ubuntu 22.04, com testes da aplicação e do binário. Sua execução remota e a validação visual ainda estão pendentes; os builds GTK de Windows/macOS ainda não foram adaptados. Os workflows abaixo foram herdados da versão Tkinter e ainda não comprovam builds GTK funcionais.

---

# LEGENDA / Linux

Interface em grafite, bordas finas e botões retos. Python 3 e Tkinter, sem pacotes pip.

Abra **LEGENDA** no menu de aplicativos do Linux, ou execute:

```sh
python3 /home/raco/legendas-linux/app.py
```

Se faltar Tkinter: no Arch, instale `tk`; no Ubuntu/Debian, `python3-tk` pelo gerenciador de pacotes.

Crie uma conta em https://www.opensubtitles.com e uma chave de aplicação em https://www.opensubtitles.com/consumers. Abra CONTA / CONFIGURAÇÕES e informe chave, usuário e senha. Credenciais não são gravadas em disco. A chave e o usuário também podem vir das variáveis OPENSUBTITLES_API_KEY e OPENSUBTITLES_USERNAME.

1. Digite o nome do filme ou série; vincular um vídeo é opcional.
2. Se necessário, ajuste o título e o idioma (pt-br, pt, en, es etc.).
3. Busque e selecione uma versão compatível com seu vídeo.
4. Baixe a legenda. Sem vídeo vinculado, escolha o destino em Salvar como. Ela fica ao lado do vídeo como `filme.pt-br.srt`, reconhecida por players como VLC e mpv.

A busca tenta identificar o arquivo pelo hash e depois pelo título. Mostra a primeira página de resultados; refine o título quando necessário. Não sobrescreve legendas existentes. O vídeo não é enviado ao serviço, apenas hash ou título. A disponibilidade, sincronização e limites diários dependem do catálogo e da conta OpenSubtitles. Nenhum catálogo contém legendas para todos os vídeos.

Documentação da API: https://opensubtitles.stoplight.io/docs/opensubtitles-api

Verificação local: compilação Python aprovada. A abertura da janela não pôde ser validada neste ambiente sem display; o display virtual também falhou. Download real exige credenciais e não foi validado sem uma conta configurada.

Testes automatizados: 8 aprovados, incluindo busca e download com respostas simuladas, hash, falha de rede, limite da API, rejeição de HTML e proteção contra sobrescrita. Execute `python3 -m unittest discover -s /home/raco/legendas-linux -v`. O atalho do menu passou em `desktop-file-validate`. Esses testes não comprovam a integração com uma conta real.

## Organização do código

- `app.py`: ponto de entrada, preservando o comando de abertura existente.
- `legenda/ui.py`: interface e execução das operações em segundo plano.
- `legenda/provider.py`: cliente REST e erros do OpenSubtitles.
- `legenda/files.py`: hash do vídeo, validação e salvamento da legenda.
- `test_app.py`: testes dos módulos e fluxos com respostas de rede simuladas.

## Builds para outros sistemas

O workflow `.github/workflows/build.yml` roda em pushes para `main`, tags `v*`, pull requests e manualmente em **Actions → Test and build desktop apps → Run workflow**.

Gera Linux x64 (Ubuntu 22.04) com GTK 4. O workflow instala PyGObject/GTK, executa os testes gráficos em D-Bus e Xvfb, empacota com PyInstaller, testa a aplicação e produz um AppImage. O pacote fica em **Artifacts** por 30 dias. Builds GTK para Windows e macOS ainda não estão disponíveis.

Para gerar localmente em Ubuntu 22.04 com GTK 4:

```sh
sudo apt-get install python3-gi python3-gi-cairo gir1.2-gtk-4.0 python3-keyring
/usr/bin/python3 -m venv --system-site-packages .venv
.venv/bin/python -m pip install -r requirements-build.txt
.venv/bin/python -m PyInstaller --noconfirm --clean --onedir --windowed --name Legenda --hidden-import=gi.repository.Gtk --hidden-import=gi.repository.Gdk --hidden-import=gi.repository.Gio --hidden-import=gi.repository.GLib app.py
```

Os testes locais passaram após a refatoração. A geração do pacote Linux e os testes gráficos precisam ser confirmados pela execução do GitHub Actions.

## AppImage e distribuições Linux

O build Linux também gera `Legenda-linux-x64.AppImage`. O workflow testa a inicialização desse mesmo pacote em Ubuntu 22.04, Ubuntu 24.04, Debian 12 e Fedora 43, usando containers com display virtual. Isso verifica bibliotecas e abertura da janela, mas não substitui testes interativos em cada desktop. Os resultados desses jobs ainda precisam ser confirmados no GitHub.

Após baixar o artefato e extrair o ZIP do GitHub:

```sh
chmod +x Legenda-linux-x64.AppImage
./Legenda-linux-x64.AppImage
```

Se FUSE estiver indisponível, use `./Legenda-linux-x64.AppImage --appimage-extract-and-run`. O AppImage é x86_64 e tem como base Ubuntu 22.04/glibc 2.35; não se promete compatibilidade com distribuições anteriores, Alpine/musl ou Linux ARM. Windows e macOS continuam com pacotes próprios.

Para produzir o AppImage, gere primeiro `dist/Legenda` no Ubuntu 22.04 e execute `bash scripts/build-appimage.sh`. O script baixa a versão `continuous` oficial do appimagetool; portanto essa ferramenta não está fixada por hash e o build não é inteiramente reprodutível.

## Publicação automática de versões

Envie uma tag `v*` para iniciar builds e publicação automática. Exemplo para a primeira versão (use um número ainda não publicado):

```sh
git push origin main
git tag v1.0.0
git push origin v1.0.0
```

Após os builds e testes Linux passarem, o job `release` publica uma GitHub Release com AppImage, pacote Linux e `SHA256SUMS.txt`. Ele usa o token automático do Actions, sem precisar cadastrar um token pessoal. A release é preparada como rascunho e publicada somente depois do upload completo. Uma nova tentativa pode continuar um rascunho; versões já publicadas não são sobrescritas. Pushes comuns em `main` geram apenas artefatos de teste, sem criar uma versão pública.

Na interface GTK, abra **Conta → Salvar no cofre** para lembrar chave API, usuário e senha. Na próxima abertura, o aplicativo recupera os dados pelo Secret Service do desktop. **Esquecer credenciais salvas** apaga os dados do cofre e limpa os campos. Não há fallback para arquivo em texto puro. Instale `python-keyring` no Arch ou `python3-keyring` no Ubuntu/Debian e mantenha um serviço compatível (como GNOME Keyring) disponível/desbloqueado. Falhas do cofre são exibidas na interface. O teste automatizado usa um cofre simulado; a integração real depende da sessão de desktop.

Botões e lista de resultados usam cursor `pointer` ao passar o mouse.
