"""Extrai somente assets, sem interpretar imagens nem roteiros. Originais abertos em rb."""
import argparse
import importlib.util
import os
from pathlib import Path, PurePosixPath
import struct
import subprocess
import sys
import zlib

ROOT = Path(__file__).resolve().parents[1]
PAC = Path(os.environ.get("EUPHORIA_PAC", "pac"))
YURIS = Path(__file__).resolve().parent / "yuris.py"
VIDEOS = ("OP", "fake", "normal_bad", "normal_good", "special_bad", "true_end")
PACOTES = ("cg", "cgsys", "se", "sn", "vo")


def carregar_yuris(caminho):
    sys.path.insert(0, str(caminho.parent))
    spec = importlib.util.spec_from_file_location("yuris_assets", caminho)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def destino_seguro(base, nome, pacote):
    nome = nome.replace("\\", "/").lower()
    partes = PurePosixPath(nome)
    if partes.is_absolute() or any(p in ("..", "") or ":" in p for p in partes.parts):
        raise ValueError("caminho inválido no pacote: " + nome)
    if not partes.parts:
        raise ValueError("nome vazio")
    # Alguns pacotes já incluem o prefixo cg/, vo/, etc.
    if partes.parts[0] != pacote:
        partes = PurePosixPath(pacote) / partes
    alvo = base.joinpath(*partes.parts)
    if not alvo.resolve().is_relative_to(base.resolve()):
        raise ValueError("destino fora da pasta do jogo")
    return alvo


def indice(caminho, trocas):
    with caminho.open("rb") as f:
        cab = f.read(32)
        if len(cab) != 32 or cab[:4] != b"YPF\0":
            raise ValueError("cabeçalho YPF inválido")
        versao, n, tamanho = struct.unpack_from("<III", cab, 4)
        if versao != 474 or not 32 <= tamanho <= caminho.stat().st_size:
            raise ValueError("versão ou índice YPF inválido")
        # v474 guarda o offset absoluto do fim do índice (inclui o cabeçalho).
        raw = f.read(tamanho - 32)
    pos = 0
    for _ in range(n):
        tam = (~raw[pos + 4]) & 255
        tam = trocas.get(tam, tam)
        nome = bytes(b ^ 255 for b in raw[pos + 5:pos + 5 + tam]).decode("cp932")
        pos += 5 + tam
        comp = raw[pos + 1]
        bruto, comprimido, offset, checksum = struct.unpack_from("<IIII", raw, pos + 2)
        pos += 18
        if offset < tamanho or offset + comprimido > caminho.stat().st_size:
            raise ValueError("entrada fora do pacote")
        yield nome, comp, bruto, comprimido, offset, checksum


def extrair_grande(caminho, destino, pacote, yuris):
    total = 0
    with caminho.open("rb") as origem:
        for nome, comp, bruto, tamanho, offset, checksum in indice(caminho, yuris.SW):
            alvo = destino_seguro(destino, nome, pacote)
            alvo.parent.mkdir(parents=True, exist_ok=True)
            parcial = alvo.with_suffix(alvo.suffix + ".parcial")
            origem.seek(offset)
            resto, escritos, soma = tamanho, 0, 1
            decoder = zlib.decompressobj() if comp else None
            try:
                with parcial.open("wb") as saida:
                    while resto:
                        bloco = origem.read(min(resto, 1024 * 1024))
                        if not bloco:
                            raise ValueError("entrada truncada")
                        resto -= len(bloco)
                        soma = zlib.adler32(bloco, soma)
                        # Limita também o buffer descomprimido por bloco.
                        while bloco:
                            dados = decoder.decompress(bloco, 1024 * 1024) if decoder else bloco
                            bloco = decoder.unconsumed_tail if decoder else b""
                            escritos += len(dados)
                            if escritos > bruto:
                                raise ValueError("tamanho descomprimido inválido")
                            saida.write(dados)
                    if decoder and (not decoder.eof or decoder.unused_data):
                        raise ValueError("zlib incompleto ou dados excedentes")
                if escritos != bruto or soma & 0xffffffff != checksum:
                    raise ValueError("tamanho/checksum inválido: " + nome)
                os.replace(parcial, alvo)
            finally:
                parcial.unlink(missing_ok=True)
            total += 1
    return total


def extrair(caminho, destino, pacote, yuris):
    if caminho.stat().st_size > 32 * 1024 * 1024:
        return extrair_grande(caminho, destino, pacote, yuris)
    # Usa a API original nos pequenos; ela lê todo o pacote em memória.
    _, entradas = yuris.ypf_ler(str(caminho))
    for entrada in entradas:
        alvo = destino_seguro(destino, entrada["nome"], pacote)
        alvo.parent.mkdir(parents=True, exist_ok=True)
        alvo.write_bytes(entrada["dado"])
    return len(entradas)


def converter_video(origem, destino, ffmpeg):
    destino.parent.mkdir(parents=True, exist_ok=True)
    parcial = destino.with_suffix(".parcial.webm")
    log = ROOT / "trabalho" / "infra" / (destino.stem + "-ffmpeg.log")
    log.parent.mkdir(parents=True, exist_ok=True)
    try:
        with log.open("w", encoding="utf-8") as f:
            subprocess.run([str(ffmpeg), "-nostdin", "-y", "-i", str(origem),
                "-map", "0:v:0", "-map", "0:a:0?", "-c:v", "libvpx-vp9",
                "-crf", "32", "-b:v", "0", "-deadline", "good", "-cpu-used", "4",
                "-row-mt", "1", "-threads", "4", "-pix_fmt", "yuv420p",
                "-c:a", "libopus", "-b:a", "128k", str(parcial)],
                stdout=f, stderr=f, check=True)
        os.replace(parcial, destino)
    finally:
        parcial.unlink(missing_ok=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--pac", type=Path, default=PAC)
    ap.add_argument("--yuris", type=Path, default=YURIS)
    ap.add_argument("--destino", type=Path, default=ROOT / "renpy/euphoria/game")
    ap.add_argument("--ffmpeg", type=Path, default=Path(r"C:\ffmpeg\bin\ffmpeg.exe"))
    ap.add_argument("--sem-videos", action="store_true")
    ap.add_argument("--so-videos", action="store_true")
    args = ap.parse_args()
    if not args.so_videos:
        yuris = carregar_yuris(args.yuris)
        for pacote in PACOTES:
            total = extrair(args.pac / (pacote + ".ypf"), args.destino, pacote, yuris)
            print(f"{pacote}: {total} arquivos", flush=True)
    if not args.sem_videos:
        for nome in VIDEOS:
            destino = args.destino / "movie" / (nome.lower() + ".webm")
            converter_video(args.pac / (nome + ".ypf"), destino, args.ffmpeg)
            print(f"vídeo: {destino.name}", flush=True)


if __name__ == "__main__":
    main()
