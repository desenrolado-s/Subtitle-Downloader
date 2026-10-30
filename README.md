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
