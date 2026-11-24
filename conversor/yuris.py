# -*- coding: utf-8 -*-
"""Euphoria (YU-RIS v474) - formato DESVENDADO e testado em 27/10/2026.

YPF v474 (pac/bn.ypf tem os 597 scripts ysbin/*.ybn):
  cabecalho 0x20: 'YPF\0', u32 versao(474), u32 n_entradas, u32 tamanho_indice
  entrada: u32 crc32(nome) | u8 ~len (com tabela de troca SW) | nome XOR 0xFF (cp932)
           | u8 tipo | u8 zlib? | u32 tam_bruto | u32 tam_comprimido | u32 offset | u32 adler32(dado comprimido)
YSTB v474 (yst00000..yst00596.ybn):
  'YSTB', u32 ver, u32 n_cmds, u32 tam_cmds, u32 tam_args, u32 tam_recursos, u32 tam_linhas, u32 0
  secoes cmds(4B: op,nargs,..) | args(12B: u16 id,u16 tipo,u32 tam,u32 offset_em_recursos) | recursos | linhas
  todas as secoes com XOR de 4 bytes (chave detectada no 1o arg, cujo offset e 0). Aqui: 78 1b 73 30.
  Fala = opcode 95, 1 arg tipo 3, recurso = b'M' + u16 tam + '"texto"' em cp932.
  Nome do falante vem DENTRO da fala: 'Rika: \u201c...\u201d'.

Biblioteca de leitura/gravacao de YPF e YSTB (YU-RIS v474), usada pelo conversor para Ren'Py.
"""
import struct, zlib

OP_FALA = 95
CHAVE = bytes.fromhex("781b7330")  # XOR dos YSTB

_T = [0x03, 0x48, 0x06, 0x35, 0x0C, 0x10, 0x11, 0x19, 0x1C, 0x1E, 0x09, 0x0B,
      0x0D, 0x13, 0x15, 0x1B, 0x20, 0x23, 0x26, 0x29, 0x2C, 0x2F, 0x2E, 0x32]
SW = {}
for i in range(0, len(_T), 2):
    SW[_T[i]], SW[_T[i + 1]] = _T[i + 1], _T[i]


# ---------------- YPF ----------------
def ypf_ler(caminho):
    d = open(caminho, "rb").read()
    assert d[:4] == b"YPF\0", "nao e YPF"
    ver, n, tam_idx = struct.unpack_from("<III", d, 4)
    o, ents = 0x20, []
    for _ in range(n):
        ini = o
        L = SW.get((~d[o + 4]) & 0xFF, (~d[o + 4]) & 0xFF)
        nome = bytes(b ^ 0xFF for b in d[o + 5:o + 5 + L]).decode("cp932")
        o += 5 + L
        tipo, comp = d[o], d[o + 1]
        bruto, tc, off, ck = struct.unpack_from("<IIII", d, o + 2)
        o += 18
        dado = d[off:off + tc]
        if comp:
            dado = zlib.decompress(dado)
        assert len(dado) == bruto, nome
        ents.append({"nome": nome, "idx": d[ini:o], "comp": comp, "dado": dado})
    return d[:0x20], ents


def ypf_gravar(cab, ents, caminho, originais=None):
    """Remonta. Entradas inalteradas reaproveitam o blob comprimido original."""
    idx_tam = sum(len(e["idx"]) for e in ents)
    off = 0x20 + idx_tam
    idx, blobs = [], []
    for e in ents:
        blob = e.get("blob_orig") if not e.get("mudou") else None
        if blob is None:
            blob = zlib.compress(e["dado"], 9) if e["comp"] else e["dado"]
        ent = bytearray(e["idx"])
        p = len(ent) - 16
        struct.pack_into("<IIII", ent, p, len(e["dado"]), len(blob), off, zlib.adler32(blob))
        idx.append(bytes(ent)); blobs.append(blob); off += len(blob)
    with open(caminho, "wb") as f:
        f.write(cab); f.write(b"".join(idx)); f.write(b"".join(blobs))


def ypf_ler_com_blobs(caminho):
    d = open(caminho, "rb").read()
    cab, ents = ypf_ler(caminho)
    for e in ents:
        tc, off = struct.unpack_from("<II", e["idx"], len(e["idx"]) - 12)
        e["blob_orig"] = d[off:off + tc]
    return cab, ents


# ---------------- YSTB ----------------
def xor(b, k):
    return bytes(c ^ k[i & 3] for i, c in enumerate(b))


def ystb_ler(dado):
    assert dado[:4] == b"YSTB"
    ver, nc, tc, ta, tr, tl, _ = struct.unpack_from("<7I", dado, 4)
    p = 0x20
    sc, sa = dado[p:p + tc], dado[p + tc:p + tc + ta]
    sr = dado[p + tc + ta:p + tc + ta + tr]
    sl = dado[p + tc + ta + tr:p + tc + ta + tr + tl]
    # chave fixa do Euphoria (igual nos 587 scripts com args). NAO detectar pelo 1o arg: depois de traduzido
    # o offset dele deixa de ser 0 e a chave sairia errada na releitura.
    k = CHAVE
    c, a, r = xor(sc, k), xor(sa, k), xor(sr, k)
    cmds, ai = [], 0
    for i in range(nc):
        op, n = c[i * 4], c[i * 4 + 1]
        args = [list(struct.unpack_from("<HHII", a, (ai + j) * 12)) for j in range(n)
                if (ai + j + 1) * 12 <= len(a)]
        cmds.append((op, ai, args)); ai += n
    return {"cab": dado[:0x20], "k": k, "c": c, "a": bytearray(a), "r": r, "l": sl, "cmds": cmds}


def ystb_falas(y):
    """[(indice_cmd, texto)] das falas."""
    out = []
    for i, (op, ai, args) in enumerate(y["cmds"]):
        if op == OP_FALA and len(args) == 1 and args[0][1] == 3:
            _, _, s, o = args[0]
            seg = y["r"][o:o + s]
            if seg[:1] == b"M" and seg[3:4] == b'"' and seg[-1:] == b'"':
                out.append((i, seg[4:-1].decode("cp932")))
    return out


def ystb_aplicar(y, novos):
    """novos: {indice_global_do_arg: recurso_novo}.
    SO ACRESCENTA: o bloco de recursos original fica intacto e os recursos novos vao para o final; so os args
    trocados tem tamanho/offset alterados. Args de tipo 0 (IF/ELSE/loops) guardam DESTINO DE SALTO no campo
    offset - reorganizar o bloco (como antes) corrompia esses saltos e o jogo travava (bug de 27/10, yst00163)."""
    a, novo = bytearray(y["a"]), bytearray(y["r"])
    for j, seg in sorted(novos.items()):
        assert struct.unpack_from("<H", a, j * 12 + 2)[0] == 3, "so args de texto (tipo 3) podem ser trocados"
        struct.pack_into("<II", a, j * 12 + 4, len(seg), len(novo))
        novo += seg
    cab = bytearray(y["cab"])
    struct.pack_into("<I", cab, 0x14, len(novo))
    k = y["k"]
    return bytes(cab) + xor(y["c"], k) + xor(bytes(a), k) + xor(bytes(novo), k) + y["l"]


def ystb_montar(y, trocas):
    """trocas: {indice_cmd: texto_novo} das falas (opcode 95)."""
    alvo = {}
    for i, txt in trocas.items():
        op, ai, args = y["cmds"][i]
        b = txt.encode("cp932")
        alvo[ai] = b"M" + struct.pack("<H", len(b) + 2) + b'"' + b + b'"'
    return ystb_aplicar(y, alvo)


# ---------------- texto ----------------
