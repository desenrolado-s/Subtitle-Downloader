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

Gera Linux x64 (Ubuntu 22.04), Windows x64 e macOS ARM64 (Apple Silicon). Cada job executa os testes, empacota com PyInstaller e abre/fecha o executável gerado como teste de inicialização. Os pacotes ficam em **Artifacts** da execução por 30 dias. Extraia todo o pacote antes de abrir: no Windows execute `Legenda.exe`, no Linux `Legenda`, no macOS `Legenda.app`. Python não precisa estar instalado na máquina de destino. Builds não são assinados nem notarizados; macOS Intel não está incluído nesta matriz.

Para gerar localmente, no sistema de destino, com Python 3.12 e Tkinter:

```sh
python -m pip install -r requirements-build.txt
python -m unittest discover -v
python -m PyInstaller --noconfirm --clean --onedir --windowed --name Legenda app.py
```

Os testes locais passaram após a refatoração. A geração dos três pacotes e os testes gráficos precisam ser confirmados pela primeira execução do GitHub Actions; configurar o workflow não comprova que os builds remotos passaram.
