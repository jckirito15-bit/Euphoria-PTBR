"""Catálogo independente do engine; I/O e validação compartilhados com os testes."""
import json
import os
import re
import tempfile
import urllib.request

MAX_BYTES = 32 * 1024 * 1024


def validar(data):
    if not isinstance(data, dict) or type(data.get("versao")) is not int or data["versao"] < 0:
        raise ValueError("versao deve ser inteiro não negativo")
    for campo in ("falas", "nomes", "escolhas"):
        itens = data.get(campo)
        if not isinstance(itens, dict) or any(not isinstance(k, str) or not isinstance(v, str) for k, v in itens.items()):
            raise ValueError("mapa de textos inválido: " + campo)
    return data


def ler(stream):
    raw = stream.read(MAX_BYTES + 1)
    if len(raw) > MAX_BYTES:
        raise ValueError("catálogo excede 32 MiB")
    return validar(json.loads(raw.decode("utf-8-sig")))


def carregar(pasta, abrir_embutido):
    if pasta:
        try:
            with open(os.path.join(pasta, "traducao.json"), "rb") as f:
                return ler(f)
        except (OSError, ValueError, UnicodeError):
            pass
    with abrir_embutido("traducao.json") as f:
        return ler(f)


def separar(texto):
    match = re.fullmatch(r'([^:\n]+):\s*[“"](.*)[”"]\s*', texto, re.S)
    return (match.group(1).strip(), match.group(2)) if match else (None, texto)


def atualizar(url, pasta, atual, publicar):
    """Executar em worker. Publicar agenda a troca do catálogo no thread principal."""
    temporario = None
    try:
        if not url or not url.startswith(("https://", "http://")):
            return
        req = urllib.request.Request(url, headers={"User-Agent": "EuphoriaPTBR/infra"})
        with urllib.request.urlopen(req, timeout=20) as resposta:
            if not resposta.geturl().startswith(("https://", "http://")):
                return
            novo = ler(resposta)
        if novo["versao"] <= atual["versao"]:
            return
        os.makedirs(pasta, exist_ok=True)
        # Não sobrescrever uma versão mais recente instalada durante a requisição.
        try:
            with open(os.path.join(pasta, "traducao.json"), "rb") as f:
                if ler(f)["versao"] >= novo["versao"]:
                    return
        except (OSError, ValueError, UnicodeError):
            pass
        fd, temporario = tempfile.mkstemp(prefix="traducao-", suffix=".tmp", dir=pasta)
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(novo, f, ensure_ascii=False)
            f.flush()
            os.fsync(f.fileno())
        os.replace(temporario, os.path.join(pasta, "traducao.json"))
        temporario = None
        publicar(novo)
    except Exception:
        # Rede, catálogo inválido e armazenamento indisponível não interrompem o jogo.
        pass
    finally:
        if temporario:
            try:
                os.unlink(temporario)
            except OSError:
                pass
