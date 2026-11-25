"""Validações antes de clonar: só repositórios públicos do GitHub e de tamanho limitado.

Com o backend exposto na internet, a URL digitada pelo usuário não pode ir direto para o `git clone`
(poderia apontar para outro host, para um caminho local ou para um repositório enorme).
"""
import re
from typing import Tuple

import httpx

from app.core.config import settings

GITHUB_URL = re.compile(r"^https://github\.com/([A-Za-z0-9](?:[A-Za-z0-9-]{0,38}))/([A-Za-z0-9._-]{1,100}?)(?:\.git)?/?$")


class RepositoryRejected(Exception):
    """O repositório não pode ser analisado; a mensagem é mostrada ao usuário."""

    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def parse_github_url(repo_url: str) -> Tuple[str, str]:
    match = GITHUB_URL.match(repo_url.strip())
    if not match or match.group(2) in (".", ".."):
        raise RepositoryRejected("Informe a URL de um repositório do GitHub, no formato https://github.com/dono/repositorio.")
    return match.group(1), match.group(2)


def ensure_repository_allowed(repo_url: str) -> str:
    """Valida a URL e o tamanho do repositório; devolve a URL de clone normalizada."""
    owner, repo = parse_github_url(repo_url)

    try:
        response = httpx.get(
            f"{settings.GITHUB_API_URL}/repos/{owner}/{repo}",
            headers={"Authorization": f"Bearer {settings.GITHUB_TOKEN}", "Accept": "application/vnd.github+json"},
            follow_redirects=True,
            timeout=15,
        )
    except httpx.HTTPError as error:
        raise RepositoryRejected("Não foi possível consultar o GitHub agora. Tente novamente.", 502) from error

    if response.status_code == 404:
        raise RepositoryRejected("Repositório não encontrado ou privado.", 404)
    if response.status_code != 200:
        raise RepositoryRejected("Não foi possível consultar o GitHub agora. Tente novamente.", 502)

    data = response.json()
    if data.get("private"):
        raise RepositoryRejected("Só repositórios públicos podem ser analisados.", 400)

    # `size` da API do GitHub vem em KB.
    size_mb = data.get("size", 0) / 1024
    if size_mb > settings.MAX_REPO_SIZE_MB:
        raise RepositoryRejected(
            f"O repositório tem cerca de {size_mb:.0f} MB; o limite desta instalação é {settings.MAX_REPO_SIZE_MB} MB.", 413)

    return f"https://github.com/{data.get('full_name', f'{owner}/{repo}')}.git"
