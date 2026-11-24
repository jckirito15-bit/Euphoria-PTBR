from pathlib import Path
import shutil
import sys
import zipfile

root = Path(__file__).resolve().parents[1]
tipo = sys.argv[1]
arquivos = list((root / "saida" / ("renpy-" + tipo)).glob("*.apk"))
if not arquivos:
    raise SystemExit("RAPT não produziu APK")
origem = max(arquivos, key=lambda p: p.stat().st_mtime_ns)
with zipfile.ZipFile(origem) as z:
    if z.testzip():
        raise SystemExit("APK corrompido")
    if tipo == "completo":
        # AAPT grava nomes UTF-8 sem marcar o bit UTF-8 do ZIP.
        def nome_android(info):
            n = info.filename
            if not info.flag_bits & 0x800:
                try:
                    n = n.encode('cp437').decode('utf-8')
                except (UnicodeError, ValueError):
                    pass
            return '/'.join(p.removeprefix('x-') for p in n.split('/'))
        nomes = {nome_android(info): info.filename for info in z.infolist()}
        if any(n.startswith("assets/game/cgsys/font/") or n.startswith("assets/game/saves/")
               or n.endswith('.rpy') or '/infra_teste/' in n
               or n in ('assets/game/script.rpyc', 'assets/game/smoke_apk.rpyc') for n in nomes):
            raise SystemExit("Arquivo excluído encontrado no APK")
        game = root / 'renpy/euphoria/game'
        total = 0
        for pasta in ('cg', 'cgsys', 'se', 'sn', 'vo', 'movie', 'cenas', 'fonts'):
            for f in (game / pasta).rglob('*'):
                if not f.is_file() or (pasta == 'cgsys' and 'font' in f.relative_to(game).parts) or f.suffix == '.rpy':
                    continue
                nome = 'assets/game/' + f.relative_to(game).as_posix()
                if nome not in nomes or z.getinfo(nomes[nome]).file_size != f.stat().st_size:
                    raise SystemExit('Asset ausente/divergente: ' + nome)
                total += 1
        for nome in ('traducao.json', 'ys_labels.json', 'config_traducao.json'):
            if z.read(nomes['assets/game/' + nome]) != (game / nome).read_bytes():
                raise SystemExit('JSON divergente: ' + nome)
        print('Assets e cenas compiladas conferidos:', total)
    proibidos = {"cenas", "movie", "cg", "cgsys", "se", "sn", "vo", "bgm", "voice"}
    if tipo == "teste" and any(proibidos.intersection(
            parte.removeprefix("x-") for parte in n.split("/")) for n in z.namelist()):
        raise SystemExit("APK de teste contém assets/cenas")
    if tipo == "teste":
        exemplo = (root / "tools/infra/traducao_exemplo.json").read_bytes()
        if z.read("assets/x-game/x-traducao.json") != exemplo:
            raise SystemExit("APK de teste não contém o catálogo fictício esperado")
if tipo == "completo" and origem.stat().st_size >= 2_000_000_000:
    raise SystemExit("APK excede o limite de 2 GB")
destino = root / "saida" / ("Euphoria-PTBR.apk" if tipo == "completo" else tipo + ".apk")
shutil.copy2(origem, destino)
print(f"APK: {destino} ({destino.stat().st_size:,} bytes)")
