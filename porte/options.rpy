define config.name = "Euphoria PT-BR"
define config.version = "0.1.0"
define config.save_directory = "euphoria-ptbr"
define config.screen_width = 1024
define config.screen_height = 768
define config.default_text_cps = 35
define config.default_fullscreen = False
define build.name = "EuphoriaPTBR"
define build.game_only_update = False

init python:
    build.classify("game/cgsys/font/**", None)
    build.classify("game/script.rpy", None)
    build.classify("game/script.rpyc", None)
    build.classify("game/**.rpy", None)
    build.classify("**/__pycache__/**", None)
    build.classify("**.pyc", None)
    build.android_permissions = ["android.permission.INTERNET"]
    build.classify("**.bak", None)
    build.classify("**.log", None)
    build.classify("**.tmp", None)
    build.classify("game/saves/**", None)
    build.classify("game/cache/**", None)
define _game_menu_screen = "menu_jogo"

init python:
    # Tela cheia: estica o jogo para ocupar a tela inteira do aparelho (sem tarjas pretas).
    def _preencher_tela(w, h):
        return (w, h)
    config.adjust_view_size = _preencher_tela
