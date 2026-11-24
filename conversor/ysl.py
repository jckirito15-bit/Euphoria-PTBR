# -*- coding: utf-8 -*-
"""Tabela de labels YSLB (ysl.ybn): 'YSLB', ver, n, u32[256] indice por hash; entradas a partir de 0x40c (indice u32[255]):
u8 len | nome cp932 | u32 hash | u32 indice_cmd | u16 script | u16 ?"""
import struct

def ler(y):
    assert y[:4] == b'YSLB'
    n = struct.unpack_from('<I', y, 8)[0]; p = 0x40c; out = []
    for _ in range(n):
        L = y[p]; nm = y[p + 1:p + 1 + L].decode('cp932'); p += 1 + L
        h, cmd, scr, x = struct.unpack_from('<IIHH', y, p); p += 12
        out.append({'nome': nm, 'hash': h, 'cmd': cmd, 'script': scr, 'x': x})
    return out
