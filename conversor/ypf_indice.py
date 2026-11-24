# -*- coding: utf-8 -*-
"""Le so o indice de um YPF grande (sem carregar dados). Retorna [(nome, comp, bruto, tam, off)]."""
import os, struct, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import yuris

def indice(caminho):
    with open(caminho, 'rb') as f:
        cab = f.read(0x20); ver, n, ti = struct.unpack_from('<III', cab, 4); raw = f.read(ti + 0x20)
    o, out = 0, []
    for _ in range(n):
        L = yuris.SW.get((~raw[o + 4]) & 0xFF, (~raw[o + 4]) & 0xFF)
        nm = bytes(b ^ 0xFF for b in raw[o + 5:o + 5 + L]).decode('cp932'); o += 5 + L
        comp = raw[o + 1]; bruto, tc, off, _ = struct.unpack_from('<IIII', raw, o + 2); o += 18
        out.append((nm, comp, bruto, tc, off))
    return out
