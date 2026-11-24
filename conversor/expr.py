# -*- coding: utf-8 -*-
"""Decodifica expressoes YSTB (args tipo 1/3): sequencia RPN de 'token u8 | len u16 | payload'."""
import struct
BIN = set('=+-*/%&|^<>,') | {'!', 'Z', 'S', 'A', 'O'}

def tokens(r):
    p = 0
    while p + 3 <= len(r):
        t = chr(r[p]); L = r[p + 1] | r[p + 2] << 8; yield t, r[p + 3:p + 3 + L]; p += 3 + L

def texto(r):
    """Lista legivel de tokens (RPN). Strings decodificadas em cp932."""
    out = []
    for t, pl in tokens(r):
        if t == 'B': out.append(str(struct.unpack('<b', pl)[0]))
        elif t == 'W': out.append(str(struct.unpack('<h', pl)[0]))
        elif t == 'I': out.append(str(struct.unpack('<i', pl)[0]))
        elif t == 'L': out.append(str(struct.unpack('<q', pl)[0]))
        elif t == 'F': out.append(repr(struct.unpack('<d', pl)[0]))
        elif t == 'M': out.append(pl.decode('cp932', 'replace'))
        elif t in 'HV': out.append('%s%s%d' % (t, chr(pl[0]), struct.unpack_from('<H', pl, 1)[0]))
        elif t == ')': out.append(')%d' % pl[0] if pl else ')')
        else: out.append(t + (pl.hex() if pl else ''))
    return ' '.join(out)
