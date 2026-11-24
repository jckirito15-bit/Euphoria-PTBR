# -*- coding: utf-8 -*-
"""Disassembler de YSTB (Euphoria / YU-RIS 474). Uso: python disasm.py yst00000 [max_cmds]"""
import os, sys, struct, json, argparse, collections
from pathlib import Path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import yuris
PAC = os.path.join(os.environ.get("EUPHORIA_PAC", "pac"), "bn.ypf")  # pasta pac do jogo original

def tabela_cmds(d):
    y = d['ysbin\ysc.ybn']; n = struct.unpack_from('<I', y, 8)[0]; o = 0x10; out = []
    for _ in range(n):
        e = y.index(b'\0', o); nm = y[o:e].decode('cp932'); o = e + 1; na = y[o]; o += 1; a = []
        for _ in range(na):
            e = y.index(b'\0', o); a.append(y[o:e].decode('cp932')); o = e + 3
        out.append((nm, a))
    return out

def carregar():
    _, e = yuris.ypf_ler(PAC)
    return {x['nome']: x['dado'] for x in e}

BINARIOS = {'+': '+', '-': '-', '*': '*', '/': '/', '%': '%', '=': '==',
            '!': '!=', '<': '<', '>': '>', 'S': '<=', 'Z': '>=',
            '&': '&&', '|': '||', '^': '^', 'A': '&', 'O': '|'}

def tokens(seg):
    """Valida os limites, inclusive caudas que o leitor básico ignorava."""
    p = 0
    out = []
    while p < len(seg):
        if p + 3 > len(seg):
            raise ValueError(f'Cabeçalho de token truncado em {p}: {seg.hex()}')
        tag, n = struct.unpack_from('<BH', seg, p)
        if p + 3 + n > len(seg):
            raise ValueError(f'Payload truncado em {p}')
        b = seg[p+3:p+3+n]
        ch = chr(tag)
        if ch in 'BWILF':
            valor = struct.unpack({'B':'<B', 'W':'<h', 'I':'<i', 'L':'<q', 'F':'<d'}[ch], b)[0]
            if ch == 'L' and abs(valor) > 2**53-1:
                valor = str(valor)
        elif ch == 'M':
            valor = b.decode('cp932')
            if len(valor) >= 2 and valor[0] == valor[-1] and valor[0] in '\"\'':
                valor = valor[1:-1]
        elif ch in 'HVv':
            if len(b) != 3:
                raise ValueError(f'Referência inválida: {b.hex()}')
            valor = [chr(b[0]), int.from_bytes(b[1:], 'little')]
        else:
            valor = b.hex()
        out.append([ch, valor])
        p += 3 + n
    return out

def infixa(ts):
    pilha, abertos = [], []
    for ch, v in ts:
        if ch in 'BWILF':
            pilha.append(str(v))
        elif ch == 'M':
            pilha.append(json.dumps(v, ensure_ascii=False))
        elif ch in 'Hv':
            pilha.append(('ref ' if ch == 'v' else '') + f'{v[0]}{v[1]}')
        elif ch == 'V':
            abertos.append((len(pilha), f'{v[0]}{v[1]}'))
        elif ch == ',':
            pass
        elif ch == ')':
            inicio, nome = abertos.pop()
            indices = pilha[inicio:]
            pilha[inicio:] = [nome + '[' + ', '.join(indices) + ']']
        elif ch in 'Rsi':
            a = pilha.pop()
            pilha.append(f'(-{a})' if ch == 'R' else f'{"str" if ch == "s" else "int"}({a})')
        elif ch in BINARIOS:
            b, a = pilha.pop(), pilha.pop()
            pilha.append(f'({a} {BINARIOS[ch]} {b})')
        else:
            raise ValueError(f'Token desconhecido: {ch!r}')
    if abertos or len(pilha) != 1:
        raise ValueError(f'Pilha final inválida: {pilha}, {abertos}')
    return pilha[0]

def tabelas(d):
    """Decodifica tabelas auxiliares; campos sem semântica confirmada ficam explícitos."""
    b = d['ysbin\\ysl.ybn']; n = struct.unpack_from('<I', b, 8)[0]
    p, labels = 12 + 256*4, {}
    for _ in range(n):
        tam = b[p]; p += 1
        nome = b[p:p+tam].decode('cp932'); p += tam
        hash_, pos, script = struct.unpack_from('<III', b, p); p += 12
        labels[nome] = {'script': script & 65535, 'flags': script >> 16, 'pos': pos, 'hash': hash_}
    assert p == len(b), ('ysl', p, len(b))
    b = d['ysbin\\ysv.ybn']; n = struct.unpack_from('<H', b, 8)[0]
    p, variaveis = 10, []
    for _ in range(n):
        escopo, script, id_, tipo, nd = struct.unpack_from('<BHHBB', b, p); p += 7
        dims = list(struct.unpack_from('<'+'I'*nd, b, p)); p += nd*4
        if tipo == 3:
            tam = struct.unpack_from('<H', b, p)[0]; p += 2
            valor = tokens(b[p:p+tam]) if tam else []; p += tam
        elif tipo in (1, 2):
            valor = struct.unpack_from('<d' if tipo == 2 else '<q', b, p)[0]; p += 8
            if tipo == 1 and abs(valor) > 2**53-1:
                valor = str(valor)
        elif tipo == 0:
            valor = None
        else:
            raise ValueError(f'Tipo de variável desconhecido em {p}: {tipo}')
        variaveis.append(dict(escopo=escopo, script=script, id=id_, tipo=tipo, dimensoes=dims, inicial=valor))
    assert p == len(b), ('ysv', p, len(b))
    b = d['ysbin\\yst_list.ybn']; n = struct.unpack_from('<I', b, 8)[0]
    p, scripts = 12, []
    for i in range(n):
        id_, tam = struct.unpack_from('<II', b, p); p += 8
        nome = b[p:p+tam].decode('cp932'); p += tam
        campos = list(struct.unpack_from('<5I', b, p)); p += 20
        scripts.append(dict(id=id_, nome=nome, campos=campos))
    assert p == len(b), ('yst_list', p, len(b))
    b = d['ysbin\\yscfg.ybn']
    sx, sy = struct.unpack_from('<II', b, 16)
    return dict(labels=labels, variaveis=variaveis, scripts=scripts,
                config={'largura':sx, 'altura':sy, 'hex':b.hex()}, comandos=tabela_cmds(d))

def decodificar(nome, bruto, tabela, falhas):
    y = yuris.ystb_ler(bruto)
    linhas, comandos = [], []
    for i, (op, ai, args) in enumerate(y['cmds']):
        nm, an = tabela[op]
        argumentos, saida = [], []
        for j, (aid, tp, sz, of) in enumerate(args):
            lab = an[aid] if aid < len(an) and an[aid] else f'arg{j}'
            a = dict(id=aid, nome=lab, tipo=tp, tamanho=sz, offset=of)
            if tp == 0:
                texto = f'metadados(size={sz}, offset={of})'
                if nm in ('IF', 'ELSE', 'LOOP'):
                    texto = f'destino=comando[{sz}], recurso={of}'
                    if sz:
                        assert sz < len(y['cmds']), (nome, i, sz)
            else:
                try:
                    a['tokens'] = tokens(y['r'][of:of+sz])
                    texto = infixa(a['tokens'])
                except (ValueError, IndexError, struct.error) as e:
                    texto = f'NAO_DECODIFICADO({y["r"][of:of+sz].hex()})'
                    falhas.append([nome, i, j, str(e)])
            argumentos.append(a)
            saida.append(f'{lab}/t{tp}: {texto}')
        comandos.append(dict(op=nm, args=argumentos))
        linhas.append(f'{i:06d} {nm} ' + ' | '.join(saida))
    return '\n'.join(linhas)+'\n', comandos

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('script', nargs='?', default='todos')
    parser.add_argument('limite', nargs='?', type=int, default=60)
    opt = parser.parse_args()
    d = carregar(); tabela = tabela_cmds(d); falhas = []
    if opt.script != 'todos':
        texto, _ = decodificar(opt.script, d[f'ysbin\\{opt.script}.ybn'], tabela, falhas)
        print('\n'.join(texto.splitlines()[:opt.limite])); return
    pasta = Path('trabalho/disasm'); pasta.mkdir(parents=True, exist_ok=True)
    exportacao = Path('app/www/dados'); exportacao.mkdir(parents=True, exist_ok=True)
    aux = tabelas(d)
    (exportacao/'tabelas.json').write_text(json.dumps(aux, ensure_ascii=False), encoding='utf-8')
    total = 0
    for nome, bruto in sorted(d.items()):
        if bruto[:4] != b'YSTB': continue
        base = Path(nome.replace('\\','/')).stem
        texto, comandos = decodificar(nome, bruto, tabela, falhas)
        (pasta/f'{base}.txt').write_text(texto, encoding='utf-8')
        (exportacao/f'{base}.json').write_text(json.dumps(comandos, ensure_ascii=False), encoding='utf-8')
        total += len(comandos)
    resumo = dict(scripts=len(list(pasta.glob('yst*.txt'))), comandos=total, falhas=falhas)
    (pasta/'resumo.json').write_text(json.dumps(resumo, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({k:v if k!='falhas' else len(v) for k,v in resumo.items()}))

if __name__ == '__main__': main()
