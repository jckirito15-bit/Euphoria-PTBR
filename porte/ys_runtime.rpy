# Runtime das cenas convertidas (tools/conversor.py).
# Cada GOSUB do YU-RIS vira ys_macro("NOME", ...). Ajuste os efeitos aqui; não precisa reconverter.
# fala()/t()/escolha() ficam em legenda.rpy (sistema de legenda atualizável).

init -10 python:
    import json, os

    # ---------- canais de áudio ----------
    renpy.music.register_channel("bgv", "voice", loop=True)
    renpy.music.register_channel("amb", "sfx", loop=True)
    renpy.music.register_channel("se2", "sfx", loop=False)

    # ---------- índice de arquivos (nome base minúsculo -> caminho) ----------
    YS_ARQ = {}
    for _f in renpy.list_files():
        _b, _e = os.path.splitext(_f.lower())
        if _e in (".png", ".webp", ".ogg", ".opus", ".webm", ".jpg"):
            YS_ARQ.setdefault(os.path.basename(_b), _f)

    def ys_arq(nome):
        if not nome:
            return None
        return YS_ARQ.get(os.path.basename(nome.replace("\\", "/")).lower())

    try:
        YS_LABELS = json.loads(renpy.file("ys_labels.json").read().decode("utf-8"))
    except Exception:
        YS_LABELS = {}

    def ys_trans(ms, mascara=None):
        ms = ms or 0
        if ms <= 0:
            return None
        m = ys_arq(mascara) if mascara else None
        if m:
            return ImageDissolve(m, ms / 1000.0, 16)
        return Dissolve(ms / 1000.0)

    def ys_com(tr):
        if tr is not None and not renpy.is_skipping():
            renpy.with_statement(tr)

# Variáveis do YU-RIS (salvas junto com o save do Ren'Py)
default ysv = {}
default ys_sel = []
default ys_sp = {}

init -9 python:
    def Y(k):
        if k in ysv:
            return ysv[k]
        nome = k[0] if isinstance(k, tuple) else k
        return "" if nome.startswith("$") else 0

    def ys_set(k, v):
        ysv[k] = v

    def ys_int(x):
        try:
            return int(x)
        except Exception:
            return 0

    def ys_div(a, b):
        if not b:
            return 0
        if isinstance(a, float) or isinstance(b, float):
            return a / b
        return int(a / b)

    def ys_go(nome):
        lb = YS_LABELS.get(nome)
        if lb and renpy.has_label(lb):
            renpy.jump(lb)
        ys_go_sistema(nome)

    def ys_go_sistema(nome):
        # Labels do sistema original (título, créditos...): volta para o menu principal.
        renpy.full_restart()

    def ys_wait(frames=None, tempo=None):
        s = (tempo / 1000.0) if tempo else ((frames or 0) / 60.0)
        if s > 0 and not renpy.is_skipping():
            renpy.pause(s, hard=False)

    def ys_escolha(ids):
        itens = [(escolha(c), i) for i, c in enumerate(ids)]
        r = renpy.display_menu(itens)
        alvo = ys_sel[r] if r < len(ys_sel) else ""
        ys_set("$1110", alvo)

    # ---------- sprites (padrão construtor do original) ----------
    # es.SP.CG.SET escolhe a imagem, X/Y/Z/A.SET ajustam o pendente, es.SP.SET.SET "NOME" mostra no slot NOME.
    YS_PEND = {}

    def ys_pend_reset():
        YS_PEND.clear()
        YS_PEND.update(arq=None, x=0, y=0, z=200.0, a=256, ms=0, mascara=None)

    ys_pend_reset()

    def ys_transform(x, y, z, a):
        z = float(z or 200.0)
        zoom = 200.0 / z if z > 0 else 1.0
        return Transform(xpos=512 + x, ypos=384 + y, xanchor=0.5, yanchor=0.5, zoom=zoom, alpha=min(1.0, (a or 0) / 256.0))

    def ys_sp_mostrar(tag):
        p = YS_PEND
        arq = ys_arq(p["arq"])
        if not arq:
            ys_pend_reset()
            return
        z = float(p["z"] or 200.0)
        renpy.show(tag, what=Image(arq), at_list=[ys_transform(p["x"], p["y"], z, p["a"])],
                   zorder=int(1000 - z * 4))
        ys_sp[tag] = dict(arq=arq, x=p["x"], y=p["y"], z=z, a=p["a"])
        ys_com(ys_trans(p["ms"] or 300, p["mascara"]))
        ys_pend_reset()

    def ys_tag_do_arquivo(arq):
        b = os.path.basename(arq or "").lower()
        if b.startswith("st_"):
            return b[3:6].upper()
        return None

    # ---------- macros ----------
    def m_bg(arq, _p2=None, ms=0, mascara="", *r):
        caminho = ys_arq(arq)
        renpy.scene()
        ys_sp.clear()
        if caminho:
            renpy.show("ys_bg", what=Image(caminho), zorder=0)
        else:
            cor = {"black": "#000", "white": "#fff", "red": "#c00"}.get((arq or "").lower(), "#000")
            renpy.show("ys_bg", what=Solid(cor), zorder=0)
        ys_com(ys_trans(ms or 0, mascara))

    def m_snd(canal, arq="", _p3=0, vol=256, p5=0, *r):
        c = int(canal or 0)
        caminho = ys_arq(arq)
        if c == 1:
            if caminho:
                renpy.music.play(caminho, channel="music", loop=True, fadein=0.5, if_changed=True)
            else:
                renpy.music.stop(channel="music", fadeout=1.0)
        elif c == 21:
            if caminho:
                renpy.music.play(caminho, channel="voice")
        elif c in (51, 52):
            if caminho:
                renpy.music.play(caminho, channel="bgv", loop=True)
            else:
                renpy.music.stop(channel="bgv", fadeout=0.5)
        elif c in (81, 82):
            if caminho:
                renpy.music.play(caminho, channel="amb", loop=True)
            else:
                renpy.music.stop(channel="amb", fadeout=0.5)
        else:
            if caminho:
                renpy.music.play(caminho, channel="sound" if c < 40 else "se2", loop=(p5 == 1))

    def m_sp_cg(_camada=None, arq=None, *r):
        YS_PEND["arq"] = arq

    def m_sp_val(campo):
        def f(_id=None, valor=0, *r):
            YS_PEND[campo] = valor if valor is not None else YS_PEND[campo]
        return f

    def m_sp_a(_id=None, alpha=256, ms=0, *r):
        YS_PEND["a"] = alpha if alpha is not None else 256
        YS_PEND["ms"] = ms or 0

    def m_sp_set(tag="SP", *r):
        ys_sp_mostrar(tag or "SP")

    def m_sp_del(tag="SP", *r):
        if renpy.showing(tag):
            renpy.hide(tag)
            ys_sp.pop(tag, None)
            ys_com(Dissolve(0.3))

    def m_sp_st(_n=None, arq=None, ms=250, *r):
        tag = ys_tag_do_arquivo(arq)
        caminho = ys_arq(arq)
        if not tag or not caminho:
            return
        info = ys_sp.get(tag)
        if info:
            renpy.show(tag, what=Image(caminho), at_list=[ys_transform(info["x"], info["y"], info["z"], info["a"])],
                       zorder=int(1000 - info["z"] * 4))
            info["arq"] = caminho
            ys_com(ys_trans(ms or 250))

    def m_fout(ms=500, mascara="", cor="black", *r):
        renpy.show("ys_fade", what=Solid({"white": "#fff", "red": "#c00"}.get((cor or "").lower(), "#000")), zorder=5000)
        ys_com(ys_trans(ms or 500, mascara))

    def m_fin(ms=500, mascara="", *r):
        if renpy.showing("ys_fade"):
            renpy.hide("ys_fade")
            ys_com(ys_trans(ms or 500, mascara))

    def m_flash(ms=500, *r):
        if not renpy.is_skipping():
            renpy.with_statement(Fade(0.05, 0.0, (ms or 500) / 1000.0, color="#fff"))

    def m_wa(ms=0, *r):
        if ms and not renpy.is_skipping():
            renpy.pause((ms or 0) / 1000.0, hard=False)

    def m_movie(arq="", *r):
        nome = os.path.splitext(os.path.basename(arq or ""))[0].lower()
        caminho = ys_arq(nome)
        if caminho:
            renpy.movie_cutscene(caminho)

    def m_sel_go(*labels):
        ys_sel[:] = list(labels)

    def m_nada(*a):
        pass

    YS_MACROS = {
        "MAC.BG": m_bg, "MAC.EV": m_bg,
        "es.SND": m_snd,
        "es.SP.CG.SET": m_sp_cg, "es.SP.X.SET": m_sp_val("x"), "es.SP.Y.SET": m_sp_val("y"),
        "es.SP.Z.SET": m_sp_val("z"), "es.SP.A.SET": m_sp_a, "es.SP.SET.SET": m_sp_set,
        "es.SP.DEL.SET": m_sp_del, "es.SP.ST.SET": m_sp_st, "es.SP.ST_G.SET": m_sp_st,
        "MAC.FOUT": m_fout, "MAC.FIN": m_fin, "MAC.FLASH": m_flash,
        "es.WA.SET": m_wa, "es.MOVIEPLAY.SET": m_movie, "ES.SEL.GO": m_sel_go,
    }

    def ys_macro(nome, *args):
        YS_MACROS.get(nome, m_nada)(*args)
