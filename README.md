<p align="center"><img src="assets/logo-professor-dazai.png" width="320" alt="Professor Dazai"></p>

# Euphoria (Clockup) — Tradução PT-BR / Brazilian Portuguese translation

**Tradução feita por Professor Dazai** · *Translation by Professor Dazai* · **Versão / Version 1.0**

Tradução completa para o português do Brasil de *Euphoria* (Clockup / MangaGamer): **34.192 falas e 53 escolhas**.

> Este repositório **não contém o jogo nem nenhum arquivo dele** (nem o APK pronto): só o texto traduzido e os
> arquivos de legenda. Você usa a sua própria cópia do jogo e o que faz com ela é por sua conta e liberdade.

## O que tem aqui

| Arquivo | Para que serve |
|---|---|
| `traducao/traducao.json` | A tradução. Formato: `{"versao": 2, "falas": {"ystNNNNN_n": "texto"}, "escolhas": {...}, "nomes": {...}}`. A chave de cada fala é o número do script do jogo (`yst`) e o número da fala nele. |
| `porte/legenda.rpy` e `porte/legenda_core.py` | O código Ren'Py que carrega o `traducao.json` e mostra cada fala (também troca caracteres sem glifo e deixa palavras gigantes quebrarem). |
| `porte/screens.rpy`, `porte/options.rpy`, `porte/ys_runtime.rpy`, `porte/ys_labels.json` | **Menus e interface em português** (Iniciar, Salvar, Carregar, Histórico, Preferências, botões da caixa de texto), o runtime do porte e a tabela de cenas. |
| `porte/COMO_ATUALIZAR_LEGENDA.txt` | Como trocar a tradução num app já instalado, sem recompilar. |
| `assets/logo-professor-dazai.png` | A logo da abertura (sem a faixa de "apoie"). |

## Como colocar a tradução (passo a passo)

A tradução é lida por um porte do jogo para **Ren'Py** (o mesmo usado no app Android). Se você já tem o porte:

1. Copie `traducao/traducao.json` para dentro da pasta `game/` do projeto Ren'Py (substitui o antigo).
2. Copie `porte/legenda.rpy`, `porte/screens.rpy`, `porte/options.rpy`, `porte/ys_runtime.rpy` e `porte/ys_labels.json` para `game/`, e `porte/legenda_core.py` para `game/python-packages/`.
3. Coloque `assets/logo-professor-dazai.png` em `game/cgsys/` com o nome `dazai1.png` (é a tela de abertura).
4. Gere o jogo de novo (PC ou APK) com o Ren'Py.

**Atualizar um app já instalado, sem recompilar:** copie o novo `traducao.json` para a pasta de saves do app
(no Android costuma ser `/sdcard/Android/data/org.euphoriaptbr.jogo/files/saves/traducao.json`); o app usa o arquivo
mais novo (veja `porte/COMO_ATUALIZAR_LEGENDA.txt`).

### Importante / Limitações da 1.0

- O **conversor do jogo original (YU-RIS) para Ren'Py não está incluído** nesta versão: o que se publica aqui é a
  tradução e o código de legenda. Sem o porte, o `traducao.json` sozinho não roda o jogo.
- O APK pronto não é distribuído porque contém os arquivos do jogo.

---

## English

Full Brazilian Portuguese translation of *Euphoria* by **Professor Dazai**: 34,192 lines and 53 choices.
No game files are included. `traducao/traducao.json` is read by a Ren'Py port (`porte/legenda.rpy`,
`porte/legenda_core.py`). Put the JSON in the project's `game/` folder, the two code files as described above, the logo
as `game/cgsys/dazai1.png`, and rebuild. To update an installed app without rebuilding, drop the new JSON in the app's
saves folder. The YU-RIS→Ren'Py converter is not part of 1.0.

## Créditos / Credits

- Tradução e projeto / Translation and project: **Professor Dazai**.
- *Euphoria* é da Clockup (edição em inglês: MangaGamer). Projeto de fãs, não oficial.

## Licença / License

MIT (código e tradução). O jogo não faz parte deste repositório.
