# -*- coding: utf-8 -*-
"""Dump legivel de um script: python dump.py <n> [ini] [fim]"""
import os, sys; sys.path.insert(0, '.'); sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import disasm, yuris, expr
d = disasm.carregar(); T = disasm.tabela_cmds(d)
def linhas(n):
    y = yuris.ystb_ler(d['ysbin\yst%05d.ybn' % n]); out = []
    for i, (op, ai, args) in enumerate(y['cmds']):
        nm, an = T[op]; s = []
        for aid, tp, sz, of in args:
            lab = an[aid] if aid < len(an) else aid
            s.append('%s=%s' % (lab, expr.texto(y['r'][of:of + sz]) if tp else '<%d,%d>' % (sz, of)))
        out.append('%d %s %s' % (i, nm, ' | '.join(s)))
    return out
if __name__ == '__main__':
    L = linhas(int(sys.argv[1])); a = int(sys.argv[2]) if len(sys.argv) > 2 else 0
    b = int(sys.argv[3]) if len(sys.argv) > 3 else len(L)
    print('\n'.join(L[a:b]))
