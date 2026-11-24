# Conversor do Euphoria (YU-RIS) para Ren'Py — passo a passo

Ferramentas de **Professor Dazai** para montar o porte do *Euphoria* (Clockup) em Ren'Py (PC e Android) a partir dos
**seus próprios arquivos do jogo**, e colocar a tradução PT-BR por cima. Nada do jogo vem neste repositório: tudo é
gerado na sua máquina.

## O que você precisa

- O jogo original *Euphoria* instalado (a pasta `pac` com `bn.ypf`, `cg.ypf`, `cgsys.ypf`, `se.ypf`, `sn.ypf`, `vo.ypf`, `OP.ypf` etc.).
- Python 3.10+ e o `ffmpeg` (para os vídeos).
- O Ren'Py 8 SDK. O script `instalar_renpy.ps1` baixa o SDK, o Java e o SDK do Android (só necessário para gerar o APK).

## Passo a passo

1. Crie uma pasta de trabalho e copie para ela a pasta `conversor/` deste repositório.
2. Diga onde está o jogo original:
   `set EUPHORIA_PAC=C:\caminho\do\Euphoria\pac`
3. Converta os scripts do jogo em cenas Ren'Py (gera `cenas/*.rpy`, `ys_labels.json` e um `traducao.json` em inglês):

   ```
   python conversor\conversor.py renpy\euphoria\game
   ```

   Deve terminar com `scripts: 456  falas: 34192  escolhas: 53`.
4. Extraia imagens, sons, vozes e converta os vídeos para o projeto:

   ```
   python conversor\extrair_assets.py --pac %EUPHORIA_PAC% --destino renpy\euphoria\game --ffmpeg C:\ffmpeg\bin\ffmpeg.exe
   ```

5. Coloque a **tradução e a interface em português** por cima (arquivos deste repositório):
   - `traducao/traducao.json` → `renpy\euphoria\game\traducao.json` (substitui o inglês do passo 3)
   - `porte/legenda.rpy`, `porte/screens.rpy`, `porte/options.rpy`, `porte/ys_runtime.rpy` → `renpy\euphoria\game\`
   - `porte/legenda_core.py` → `renpy\euphoria\game\python-packages\`
   - `assets/logo-professor-dazai.png` → `renpy\euphoria\game\cgsys\dazai1.png` (abertura)
   - uma fonte `fonts\NotoSans-Regular.ttf` (vem com o Ren'Py SDK) em `renpy\euphoria\game\fonts\`
6. Abra a pasta `renpy\euphoria` no Ren'Py (ou rode `build_apk.bat` para gerar o APK Android).

## O que foi conferido e o que não

- **Conferido:** o passo 3 gera as 456 cenas exatamente iguais (byte a byte) às do porte que gerou o APK
  *Euphoria PT-BR*, com 34.192 falas e 53 escolhas; a tabela de labels também sai idêntica.
- **Não refeito nesta publicação:** os passos 4 a 6 (extração de assets, montagem e build do APK) foram feitos antes
  com estas mesmas ferramentas, mas não foram repetidos do zero agora. Se algo falhar nessa parte, abra uma issue.

## Arquivos

| Arquivo | Função |
|---|---|
| `yuris.py` | Leitura/gravação de YPF e YSTB (formato YU-RIS v474) |
| `disasm.py`, `expr.py`, `ysl.py`, `dump.py` | Desmontagem dos scripts, expressões e tabela de labels |
| `conversor.py` | Scripts YU-RIS → cenas Ren'Py + `traducao.json` |
| `extrair_assets.py`, `ypf_indice.py` | Extração de imagens, sons, vozes e vídeos dos `.ypf` |
| `comprimir.py`, `finalizar_apk.py`, `build_apk.bat`, `build_dados.bat`, `instalar_renpy.ps1` | Build do APK Android |
