init python:
    class SegurarSkip(renpy.Displayable):
        def render(self, width, height, st, at):
            rv = renpy.Render(270, 64)
            rv.blit(renpy.render(Solid("#29435f"), 270, 64, st, at), (0, 0))
            rv.blit(renpy.render(Text("Segure para pular", size=24), 260, 64, st, at), (10, 16))
            return rv

        def event(self, ev, x, y, st):
            import pygame_sdl2 as pygame
            if ev.type == pygame.MOUSEBUTTONUP and ev.button == 1:
                config.skipping = None
            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1 and 0 <= x < 270 and 0 <= y < 64:
                config.skipping = "slow"
                renpy.restart_interaction()
                raise renpy.IgnoreEvent()

    config.overlay_screens.append("quick_menu")

style default:
    font "fonts/NotoSans-Regular.ttf"
    size 30
    color "#ffffff"
    outlines [(2, "#000000", 0, 0)]

style button:
    background Solid("#00000099")
    hover_background Solid("#000000cc")
    padding (22, 12)
    yminimum 64

style button_text:
    size 28
    hover_color "#b9e5ff"
    selected_color "#80d8ff"

style say_dialogue:
    size 30
    color "#f4f4f4"
    outlines [(2, "#000000aa", 0, 0)]
    line_spacing 6
    xmaximum 900
style say_label:
    size 28
    color "#ffd9a0"
    bold True
    outlines [(2, "#000000aa", 0, 0)]

style qbtn is button:
    background None
    hover_background Solid("#ffffff18")
    padding (14, 6)
    yminimum 44
style qbtn_text:
    size 20
    color "#ffffffaa"
    hover_color "#ffd9a0"
    selected_color "#ffd9a0"
    outlines [(1, "#000000", 0, 0)]

screen say(who, what):
    window:
        id "window"
        background Solid("#00000073")
        xfill True
        yalign 1.0
        yminimum 230
        padding (0, 0, 0, 56)
        vbox:
            xpos 62
            ypos 28
            xmaximum 900
            spacing 6
            if who is not None:
                text who id "who"
            text what id "what"

screen quick_menu():
    zorder 100
    if not main_menu:
        hbox:
            xalign 0.97
            yalign 0.995
            spacing 2
            textbutton "Auto" style "qbtn" action Preference("auto-forward", "toggle")
            textbutton "Pular" style "qbtn" action Skip() alternate Skip(fast=True, confirm=True)
            textbutton "Log" style "qbtn" action ShowMenu("historico")
            textbutton "Salvar" style "qbtn" action ShowMenu("save")
            textbutton "Carregar" style "qbtn" action ShowMenu("load")
            textbutton "Menu" style "qbtn" action ShowMenu("menu_jogo")

screen choice(items):
    modal True
    vbox:
        xalign 0.5
        yalign 0.4
        spacing 20
        for i in items:
            textbutton i.caption action i.action xminimum 640

label main_menu:
    call screen main_menu
    return

screen main_menu():
    tag menu
    add "cgsys/title/back.png"
    frame:
        background Solid("#00000080")
        xalign 0.92
        yalign 0.62
        padding (20, 16)
        xsize 230
        ysize 250
    vbox:
        xalign 0.92
        yalign 0.62
        spacing 6
        for nome, acao in [("start", Start("start")), ("load", ShowMenu("load")),
                           ("config", ShowMenu("preferences")), ("end", Quit(confirm=False))]:
            imagebutton:
                id "title_" + nome
                idle "cgsys/title/btn_%s_off.png" % nome
                hover "cgsys/title/btn_%s_over.png" % nome
                action acao

screen menu_jogo():
    tag menu
    modal True
    add Solid("#000c")
    vbox:
        xalign 0.5
        yalign 0.5
        spacing 18
        text "Menu" size 48 xalign 0.5
        textbutton "Continuar" action Return() xminimum 600
        textbutton "Salvar" action ShowMenu("save") xminimum 600
        textbutton "Carregar" action ShowMenu("load") xminimum 600
        textbutton "Histórico" action ShowMenu("historico") xminimum 600
        textbutton "Preferências" action ShowMenu("preferences") xminimum 600
        textbutton "Menu principal" action MainMenu() xminimum 600

screen save():
    tag menu
    use slots("Salvar")

screen load():
    tag menu
    use slots("Carregar")

screen slots(titulo):
    modal True
    add Solid("#101b2b")
    vbox:
        xalign 0.5
        ypos 20
        spacing 14
        text "[titulo]" size 44 xalign 0.5
        grid 3 2:
            spacing 16
            for i in range(1, 7):
                $ slot = i
                button:
                    xsize 320
                    ysize 280
                    action FileAction(slot)
                    vbox:
                        add FileScreenshot(slot) xsize 288 ysize 216
                        text FileTime(slot, format="%d/%m/%y %H:%M", empty="Vazio") size 24
        hbox:
            xalign 0.5
            spacing 10
            textbutton "<" action FilePagePrevious()
            for p in range(1, 11):
                textbutton "[p]" action FilePage(p)
            textbutton ">" action FilePageNext()
            textbutton "Voltar" action Return()

screen historico():
    tag menu
    modal True
    add Solid("#101b2b")
    viewport:
        xalign 0.5
        ypos 20
        xsize 960
        ysize 600
        scrollbars "vertical"
        mousewheel True
        draggable True
        yinitial 1.0
        vbox:
            spacing 14
            for h in _history_list:
                vbox:
                    if h.who:
                        text h.who color "#80d8ff" size 28
                    text h.what size 28
    textbutton "Voltar" action Return() xalign 0.5 yalign 0.98

screen preferences():
    tag menu
    add Solid("#172337")
    vbox:
        xalign 0.5
        yalign 0.5
        spacing 16
        text "Preferências" size 44
        text "Velocidade do texto"
        bar value Preference("text speed") xsize 650 ysize 36
        textbutton "Pular texto não lido" action Preference("skip", "toggle")
        textbutton "Recarregar tradução" action [Function(recarregar_traducao), Notify("Tradução recarregada.")]
        text ("Versão da tradução: %s" % _catalogo["versao"]) size 24
        textbutton "Menu principal" action MainMenu(confirm=False)
        textbutton "Voltar" action Return()

screen confirm(message, yes_action, no_action):
    modal True
    add Solid("#000b")
    vbox:
        xalign 0.5
        yalign 0.5
        spacing 24
        text message
        textbutton "Sim" action yes_action
        textbutton "Não" action no_action

screen notify(message):
    zorder 200
    text message xalign 0.5 ypos 25
    timer 3.0 action Hide("notify")
