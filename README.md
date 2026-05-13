# Popper 3

Aplicativo desktop para criar baralhos, cadastrar cartas e gerar PDFs em A4 para impressão.

## Recursos

- Banco local SQLite em `%LOCALAPPDATA%\Popper 3\data\popper3.db`.
- Cadastro de baralhos com nome e capa.
- Cartas de jogo e cartas de jogador.
- Splash art em PNG, JPG, JPEG ou SVG.
- PDF de impressão com cartas de 6,9 cm x 9,6 cm em folha A4.
- Relatório PDF das cartas de jogo com título, pontuação e veracidade.
- Geração de modelo Excel e importação de cartas de jogo.

## Executar em desenvolvimento

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m popper3
```

## Gerar executável Windows

```powershell
pip install pyinstaller
pyinstaller --noconfirm --windowed --name "Popper 3" --add-data "popper3;popper3" popper3/__main__.py
```

O executável ficará em `dist/Popper 3/Popper 3.exe`.
