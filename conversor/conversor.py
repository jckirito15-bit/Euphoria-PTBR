# -*- coding: utf-8 -*-
"""Conversor YU-RIS (Euphoria) -> Ren'Py.

Gera renpy/euphoria/game/cenas/yst_NNNNN.rpy para cada script de história (data\\script\\userscript\\)
e renpy/euphoria/game/traducao.json com as falas e escolhas (ID estável = ystNNNNN_c<indice_cmd>).

O conversor só traduz fluxo (IF/ELSE/GO/END), variáveis (LET), falas, escolhas e chamadas de macro.
A semântica das macros (fundo, sprites, som, fades...) fica em game/ys_runtime.rpy: cada GOSUB vira
`$ ys_macro("NOME", arg1, arg2, ...)`, então dá para ajustar efeitos sem reconverter.

Uso: python conversor.py [saida]   (padrão: renpy/euphoria/game; defina EUPHORIA_PAC = pasta "pac" do jogo original)
"""
import json, os, re, struct, sys, hashlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import disasm, yuris, ysl

SAIDA = sys.argv[1] if len(sys.argv) > 1 else os.path.join("renpy", "euphoria", "game")

BIN = {'+': '+', '-': '-', '*': '*', '/': '//', '%': '%', '<': '<', '>': '>', '=': '==', '!': '!=',
       'S': '<=', 'Z': '>=', '&': 'and', '|': 'or', 'A': '&', 'O': '|', '^': '^'}


# ---------------- expressões ----------------
def var_chave(t, pl, idx=None):
    nome = '%s%d' % (chr(pl[0]), struct.unpack_from('<H', pl, 1)[0])
    return repr(nome) if idx is None else '(%r, %s)' % (nome, ', '.join(idx))


def expr_py(r, como_alvo=False):
    """RPN -> expressão Python. Leitura de variável: Y(chave). Se como_alvo, devolve só a chave."""
    pilha, abertos = [], []
    p = 0
    while p + 3 <= len(r):
        t = chr(r[p]); L = r[p + 1] | r[p + 2] << 8; pl = r[p + 3:p + 3 + L]; p += 3 + L
        if t == 'B': pilha.append(str(struct.unpack('<b', pl)[0]))
        elif t == 'W': pilha.append(str(struct.unpack('<h', pl)[0]))
        elif t == 'I': pilha.append(str(struct.unpack('<i', pl)[0]))
        elif t == 'L': pilha.append(str(struct.unpack('<q', pl)[0]))
        elif t == 'F': pilha.append(repr(struct.unpack('<d', pl)[0]))
        elif t == 'M':
            s = pl.decode('cp932', 'replace')
            if len(s) >= 2 and s[0] in '"\'' and s[-1] == s[0]: s = s[1:-1]
            pilha.append(repr(s))
        elif t == 'H': pilha.append(('K', var_chave(t, pl)))
        elif t in 'Vv':
            abertos.append((pl, len(pilha)))
        elif t == ',':
            pass  # separador de índices: os índices já estão na pilha
        elif t == ')':
            pl0, base = abertos.pop()
            idx = [fmt(x) for x in pilha[base:]]; del pilha[base:]
            pilha.append(('K', var_chave('V', pl0, idx)))
        elif t == 'R': pilha.append('(-%s)' % fmt(pilha.pop()))
        elif t == 's': pilha.append('str(%s)' % fmt(pilha.pop()))
        elif t == 'i': pilha.append('ys_int(%s)' % fmt(pilha.pop()))
        elif t in BIN:
            b = fmt(pilha.pop()); a = fmt(pilha.pop())
            pilha.append('ys_div(%s, %s)' % (a, b) if t == '/' else '(%s %s %s)' % (a, BIN[t], b))
        else:
            raise ValueError('token desconhecido %r' % t)
    if not pilha:
        return None
    x = pilha[-1]
    if como_alvo:
        return x[1] if isinstance(x, tuple) else x
    return fmt(x)


def fmt(x):
    return 'Y(%s)' % x[1] if isinstance(x, tuple) else x


# ---------------- labels ----------------
def nome_label(n):
    """Label YU-RIS -> identificador Ren'Py estável."""
    base = re.sub(r'[^0-9A-Za-z_]', '_', n)
    if base != n or not base or base[0].isdigit():
        base = base + '_' + hashlib.md5(n.encode('utf-8')).hexdigest()[:6]
    return 'L_' + base


def main():
    d = disasm.carregar(); T = disasm.tabela_cmds(d)
    labels = ysl.ler(d['ysbin\\ysl.ybn'])
    lista = {}  # id do script -> arquivo-fonte original (yst_list.ybn)
    b = d['ysbin\yst_list.ybn']; p = 12
    for _ in range(struct.unpack_from('<I', b, 8)[0]):
        i, tam = struct.unpack_from('<II', b, p); p += 8
        lista[i] = b[p:p + tam].decode('cp932'); p += tam + 20
    historia = sorted(i for i, nm in lista.items() if '\\userscript\\' in nm)
    por_script = {}
    for lb in labels:
        por_script.setdefault(lb['script'], {}).setdefault(lb['cmd'], []).append(lb['nome'])
    labels_historia = {lb['nome'] for lb in labels if lb['script'] in historia}

    os.makedirs(os.path.join(SAIDA, 'cenas'), exist_ok=True)
    falas, escolhas, avisos = {}, {}, []
    mapa_labels = {}

    for n in historia:
        chave = 'ysbin\\yst%05d.ybn' % n
        if chave not in d:
            avisos.append('yst%05d ausente no bn.ypf' % n); continue
        y = yuris.ystb_ler(d[chave])
        out = ['# gerado por tools/conversor.py a partir de %s' % lista[n], '']
        nivel = 1
        out.append('label yst_%05d:' % n)
        aberto_label = True

        def emit(s):
            out.append('    ' * nivel + s)

        def arg(args, i):
            aid, tp, sz, of = args[i]
            return expr_py(y['r'][of:of + sz]) if tp else None

        if n == historia[0] or lista[n].endswith('\\start.txt'):
            pass
        for i, (op, ai, args) in enumerate(y['cmds']):
            for lb in por_script.get(n, {}).get(i, []):
                mapa_labels[lb] = nome_label(lb)
                if nivel > 1:
                    avisos.append('yst%05d: label %s dentro de bloco (nivel %d)' % (n, lb, nivel))
                out.append('    ' * (nivel - 1) + 'label %s:' % nome_label(lb))
                aberto_label = True
            if not aberto_label:
                out.append('label yst_%05d:' % n); aberto_label = True
            nm, an = T[op]
            try:
                if nm == '_':
                    aid, tp, sz, of = args[0]
                    seg = y['r'][of:of + sz]
                    txt = seg[4:-1].decode('cp932') if seg[:1] == b'M' else seg.decode('cp932', 'replace')
                    fid = 'yst%05d_c%d' % (n, i)
                    falas[fid] = txt
                    emit('$ fala(%r)' % fid)
                elif nm == 'RETURNCODE' or nm == 'WORD':
                    continue
                elif nm == 'GOSUB':
                    alvo = arg(args, 0)
                    params = []
                    for j in range(1, len(args)):
                        params.append(arg(args, j) or 'None')
                    alvo_s = eval(alvo) if alvo and alvo[0] in '\'"' else None
                    if alvo_s == 'ES.SEL.SET':
                        ids = []
                        for k, pexpr in enumerate(params):
                            if pexpr not in ("''", 'None'):
                                cid = 'yst%05d_c%d_%d' % (n, i, k)
                                escolhas[cid] = eval(pexpr).strip().strip('“”"').strip()
                                ids.append(cid)
                        emit('$ ys_escolha(%r)' % ids)
                    elif alvo_s:
                        emit('$ ys_macro(%s)' % ', '.join([repr(alvo_s)] + params))
                    else:
                        emit('$ ys_macro(%s)' % ', '.join([alvo] + params))
                elif nm == 'GO':
                    alvo = arg(args, 0)
                    if alvo and alvo[0] in '\'"':
                        lb = eval(alvo)
                        if lb in labels_historia:
                            emit('jump %s' % nome_label(lb))
                        else:
                            emit('$ ys_go_sistema(%r)' % lb)
                    else:
                        emit('$ ys_go(%s)' % alvo)
                elif nm == 'LET':
                    alvo = expr_py(y['r'][args[0][3]:args[0][3] + args[0][2]], como_alvo=True)
                    emit('$ ys_set(%s, %s)' % (alvo, arg(args, 1)))
                elif nm == 'IF':
                    emit('if %s:' % (arg(args, 0) or 'True')); nivel += 1; emit('pass')
                elif nm == 'IFBLEND':
                    continue
                elif nm == 'ELSE':
                    nivel -= 1
                    cond = arg(args, 0) if args and args[0][1] else None
                    emit('elif %s:' % cond if cond else 'else:'); nivel += 1; emit('pass')
                elif nm == 'IFEND':
                    nivel -= 1
                elif nm == 'END':
                    emit('return')
                elif nm == 'WAIT':
                    emit('$ ys_wait(%s)' % ', '.join(arg(args, j) or 'None' for j in range(len(args))))
                else:
                    avisos.append('yst%05d:%d comando %s ignorado' % (n, i, nm))
                    emit('# %s ignorado' % nm)
            except Exception as e:
                avisos.append('yst%05d:%d %s: %s' % (n, i, nm, e))
                emit('# ERRO %s: %s' % (nm, e))
        out.append('    return')
        open(os.path.join(SAIDA, 'cenas', 'yst_%05d.rpy' % n), 'w', encoding='utf-8').write('\n'.join(out) + '\n')

    # início do jogo: start.txt
    ini = [i for i in historia if lista[i].endswith('\\start.txt')][0]
    open(os.path.join(SAIDA, 'cenas', 'inicio.rpy'), 'w', encoding='utf-8').write(
        '# gerado por tools/conversor.py\nlabel start:\n    jump yst_%05d\n' % ini)
    trad = {'versao': 1, 'falas': falas, 'escolhas': escolhas, 'nomes': {}}
    json.dump(trad, open(os.path.join(SAIDA, 'traducao.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
    json.dump(mapa_labels, open(os.path.join(SAIDA, 'ys_labels.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
    open(os.path.join(SAIDA, 'avisos_conversor.txt'), 'w', encoding='utf-8').write('\n'.join(avisos))
    print('scripts: %d  falas: %d  escolhas: %d  labels: %d  avisos: %d'
          % (len(historia), len(falas), len(escolhas), len(mapa_labels), len(avisos)))


if __name__ == '__main__':
    main()
