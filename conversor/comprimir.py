# -*- coding: utf-8 -*-
"""Comprime os assets extraídos para caber num APK só (< 2 GB).
cg/**/*.png -> .webp (qualidade 88, alpha preservado); vo/**/*.ogg -> .opus (libopus 40 kbps).
Substitui no lugar (os originais continuam nos .ypf; refaça com tools/extrair_assets.py se precisar).
Uso: python comprimir.py [pasta_game]"""
import os, subprocess, sys
from concurrent.futures import ProcessPoolExecutor
from PIL import Image

GAME = sys.argv[1] if len(sys.argv) > 1 else os.path.join("renpy", "euphoria", "game")
FFMPEG = r"C:\ffmpeg\bin\ffmpeg.exe"


def png(p):
    q = p[:-4] + ".webp"
    try:
        with Image.open(p) as im:
            im.save(q, "WEBP", quality=88, method=4)
        os.remove(p)
        return 0
    except Exception as e:
        return "%s: %s" % (p, e)


def ogg(p):
    q = p[:-4] + ".opus"
    r = subprocess.run([FFMPEG, "-v", "error", "-y", "-i", p, "-c:a", "libopus", "-b:a", "40k", q],
                       capture_output=True)
    if r.returncode == 0 and os.path.getsize(q) > 0:
        os.remove(p)
        return 0
    return "%s: %s" % (p, r.stderr.decode("utf-8", "replace")[:200])


def arquivos(pasta, ext):
    for raiz, _, fs in os.walk(os.path.join(GAME, pasta)):
        for f in fs:
            if f.lower().endswith(ext):
                yield os.path.join(raiz, f)


if __name__ == "__main__":
    tarefas = [(png, p) for p in arquivos("cg", ".png")] + [(ogg, p) for p in arquivos("vo", ".ogg")]
    print("arquivos:", len(tarefas), flush=True)
    erros = 0
    with ProcessPoolExecutor(14) as ex:
        futs = [ex.submit(f, p) for f, p in tarefas]
        for i, fu in enumerate(futs, 1):
            r = fu.result()
            if r:
                erros += 1; print("ERRO", r, flush=True)
            if i % 1000 == 0:
                print(i, "/", len(tarefas), flush=True)
    print("fim. erros:", erros)
