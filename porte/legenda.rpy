init -10 python:
    import json
    import legenda_core

    _catalogo = legenda_core.carregar(None, renpy.open_file)

    def t(chave):
        return _catalogo["falas"].get(chave, "[" + chave + "]")

    def nome(original):
        return _catalogo["nomes"].get(original, original)

    def escolha(chave):
        return limpar(_catalogo["escolhas"].get(chave, "[" + chave + "]"))

    import re as _re
    # Caracteres que a NotoSans nao tem (apareciam quebrados na legenda).
    _TROCAS = {u"／": "/", u"　": " ", u"■": "*", u"♪": "~"}

    def limpar(s):
        for a, b in _TROCAS.items():
            s = s.replace(a, b)
        s = _re.sub(u"[぀-ヿ㐀-鿿ｦ-ﾟ]+", "", s)
        s = s.replace(u"‘’", "")
        # palavras gigantes (gritos) sem espaco vazavam da tela: permite quebrar
        return _re.sub(r"(\S{24})(?=\S)", r"\1" + u"​", s)

    def fala(chave):
        who, what = legenda_core.separar(t(chave))
        # Dados remotos são texto literal, sem tags Ren'Py ou interpolação de código.
        if who is not None:
            who = limpar(nome(who)).replace("[", "[[").replace("{", "{{")
        what = limpar(what).replace("==", "—").replace("[", "[[").replace("{", "{{")
        renpy.say(who, what)

    def recarregar_traducao():
        global _catalogo
        _catalogo = legenda_core.carregar(config.savedir, renpy.open_file)
        renpy.restart_interaction()

    def _publicar_traducao(novo):
        global _catalogo
        if novo["versao"] > _catalogo["versao"]:
            _catalogo = novo
            renpy.restart_interaction()

    def iniciar_traducao():
        recarregar_traducao()
        try:
            with renpy.open_file("config_traducao.json") as f:
                url = json.load(f).get("url", "")
            if url:
                def worker():
                    legenda_core.atualizar(url, config.savedir, _catalogo,
                        lambda novo: renpy.invoke_in_main_thread(_publicar_traducao, novo))
                renpy.invoke_in_thread(worker)
        except Exception:
            pass

    config.after_load_callbacks.append(recarregar_traducao)

label splashscreen:
    $ iniciar_traducao()
    return
