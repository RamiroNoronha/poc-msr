"""Identificação de desenvolvedores e sugestão de identidades que parecem ser a mesma pessoa.

Uma "identidade" é um par (nome, e-mail) como aparece nos commits. A mesma pessoa costuma
ter várias (nomes diferentes, e-mails pessoais e de trabalho, usuário do GitHub...).
"""
import re
import unicodedata
from collections import Counter, defaultdict
from difflib import SequenceMatcher
from typing import Any, Dict, List, Set, Tuple

# Comparações aproximadas só entre as identidades mais ativas, para limitar o custo.
FUZZY_CANDIDATES = 300
HANDLE_SIMILARITY = 0.72
NAME_SIMILARITY = 0.9
MIN_HANDLE_LENGTH = 4
# Nomes de uma palavra só com este tamanho ou mais (ex.: "RamiroNoronhaDti") são tratados como identificadores únicos.
LONG_SINGLE_NAME = 8

GENERIC_HANDLES = {
    "admin", "root", "git", "info", "noreply", "no-reply", "dev", "user", "me",
    "ubuntu", "nobody", "support", "mail", "contact", "github", "unknown", "none",
}
NOREPLY_PATTERN = re.compile(r"^(?:\d+\+)?([^@]+)@users\.noreply\.github\.com$", re.IGNORECASE)

HIGH = "high"
MEDIUM = "medium"


def identity_id(name: str, email: str) -> str:
    return f"{name} <{email.strip().lower()}>"


def _fold(text: str) -> str:
    decomposed = unicodedata.normalize("NFKD", text)
    return "".join(char for char in decomposed if not unicodedata.combining(char)).casefold()


def _tokens(name: str) -> List[str]:
    return re.findall(r"[a-z0-9]+", _fold(name))


def _handle(email: str) -> Tuple[str, str]:
    """Devolve (usuário do e-mail normalizado, login do GitHub se for e-mail noreply)."""
    email = email.strip().lower()
    match = NOREPLY_PATTERN.match(email)
    if match:
        login = re.sub(r"[^a-z0-9]", "", match.group(1).lower())
        return login, login

    local = email.split("@")[0].split("+")[0]
    return re.sub(r"[^a-z0-9]", "", local), ""


def list_developers(commits: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    counts: Counter = Counter()
    for commit in commits:
        counts[(commit.get("author", ""), commit.get("email", "").strip().lower())] += 1

    developers = [
        {"id": identity_id(name, email), "name": name, "email": email, "commits": count}
        for (name, email), count in counts.items()
    ]
    return sorted(developers, key=lambda dev: (-dev["commits"], dev["name"], dev["email"]))


class _UnionFind:
    def __init__(self, size: int):
        self.parent = list(range(size))

    def find(self, item: int) -> int:
        while self.parent[item] != item:
            self.parent[item] = self.parent[self.parent[item]]
            item = self.parent[item]
        return item

    def union(self, a: int, b: int) -> None:
        self.parent[self.find(a)] = self.find(b)


def suggest_groups(developers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Sugere grupos de identidades que podem ser a mesma pessoa.

    - "high": sinais fortes (mesmo e-mail, mesmo nome completo, mesmo usuário do GitHub).
    - "medium": sinais fracos (só o primeiro nome, usuário do e-mail parecido com o nome...).
      Um grupo "medium" contém também os grupos "high" que ele liga.
    """
    infos = []
    for developer in developers:
        tokens = _tokens(developer["name"])
        handle, login = _handle(developer["email"])
        infos.append({"tokens": tokens, "joined": "".join(tokens), "handle": handle, "login": login})

    edges: Dict[Tuple[int, int], Tuple[str, str]] = {}

    def link(a: int, b: int, confidence: str, reason: str) -> None:
        key = (min(a, b), max(a, b))
        if key[0] == key[1]:
            return
        current = edges.get(key)
        if current is None or (current[0] == MEDIUM and confidence == HIGH):
            edges[key] = (confidence, reason)

    def link_buckets(key_of, confidence: str, reason: str) -> None:
        buckets: Dict[str, List[int]] = defaultdict(list)
        for index in range(len(developers)):
            key = key_of(index)
            if key:
                buckets[key].append(index)
        for members in buckets.values():
            for other in members[1:]:
                link(members[0], other, confidence, reason)

    def usable_handle(index: int) -> str:
        handle = infos[index]["handle"]
        return handle if len(handle) >= MIN_HANDLE_LENGTH and handle not in GENERIC_HANDLES else ""

    emails = [developer["email"].strip().lower() for developer in developers]
    link_buckets(lambda i: emails[i] if usable_handle(i) else "", HIGH, "same_email")
    link_buckets(lambda i: infos[i]["joined"] if len(infos[i]["tokens"]) >= 2 or len(infos[i]["joined"]) >= LONG_SINGLE_NAME else "",
                 HIGH, "same_name")
    link_buckets(lambda i: infos[i]["login"], HIGH, "same_github_login")
    link_buckets(lambda i: infos[i]["joined"] if len(infos[i]["tokens"]) == 1 and 3 <= len(infos[i]["joined"]) < LONG_SINGLE_NAME else "",
                 MEDIUM, "same_single_name")
    link_buckets(usable_handle, MEDIUM, "same_email_user")

    candidates = range(min(len(developers), FUZZY_CANDIDATES))
    for a in candidates:
        for b in range(a + 1, len(candidates)):
            _compare_fuzzy(a, b, infos, link)

    return _build_groups(developers, edges)


def _compare_fuzzy(a: int, b: int, infos: List[Dict[str, Any]], link) -> None:
    first, second = infos[a], infos[b]

    for single, full, single_index, full_index in ((first, second, a, b), (second, first, b, a)):
        if len(single["tokens"]) == 1 and len(single["joined"]) >= 3 and len(full["tokens"]) >= 2 \
                and full["tokens"][0] == single["joined"]:
            link(single_index, full_index, MEDIUM, "first_name_only")

    for handle_owner, name_owner, handle_index, name_index in ((first, second, a, b), (second, first, b, a)):
        handle = handle_owner["handle"]
        has_full_name = len(name_owner["tokens"]) >= 2 or len(name_owner["joined"]) >= LONG_SINGLE_NAME
        if len(handle) < MIN_HANDLE_LENGTH or handle in GENERIC_HANDLES or not has_full_name:
            continue
        if handle == name_owner["joined"]:
            link(handle_index, name_index, HIGH, "handle_matches_name")
        elif SequenceMatcher(None, handle, name_owner["joined"]).ratio() >= HANDLE_SIMILARITY:
            link(handle_index, name_index, MEDIUM, "handle_similar_to_name")

    if len(first["tokens"]) >= 2 and len(second["tokens"]) >= 2 and first["joined"] != second["joined"] \
            and SequenceMatcher(None, first["joined"], second["joined"]).ratio() >= NAME_SIMILARITY:
        link(a, b, MEDIUM, "similar_name")


def _clusters(size: int, edges: List[Tuple[Tuple[int, int], Tuple[str, str]]]) -> List[Dict[str, Any]]:
    """Agrupa as identidades ligadas por arestas; guarda os motivos por nível de confiança."""
    union_find = _UnionFind(size)
    for (a, b), _ in edges:
        union_find.union(a, b)

    clusters: Dict[int, Dict[str, Any]] = {}
    for (a, b), (confidence, reason) in edges:
        cluster = clusters.setdefault(
            union_find.find(a), {"members": set(), "reasons": {HIGH: set(), MEDIUM: set()}})
        cluster["members"].update((a, b))
        cluster["reasons"][confidence].add(reason)

    return list(clusters.values())


def _build_groups(developers: List[Dict[str, Any]], edges: Dict[Tuple[int, int], Tuple[str, str]]) -> List[Dict[str, Any]]:
    high_edges = [item for item in edges.items() if item[1][0] == HIGH]
    candidates = []

    def add(cluster: Dict[str, Any], confidence: str) -> None:
        members = cluster["members"]
        candidates.append({
            "ids": [developers[i]["id"] for i in sorted(members)],
            "confidence": confidence,
            "reasons": sorted(cluster["reasons"][confidence]),
            "commits": sum(developers[i]["commits"] for i in members),
        })

    high_clusters = _clusters(len(developers), high_edges)
    for cluster in high_clusters:
        add(cluster, HIGH)

    # Grupos "medium": ligados por qualquer sinal, com ao menos um sinal fraco. Contêm os grupos "high" que ligam.
    # Só valem se acrescentarem identidades além de um grupo "high" que já exista.
    high_members = [cluster["members"] for cluster in high_clusters]
    for cluster in _clusters(len(developers), list(edges.items())):
        if cluster["reasons"][MEDIUM] and cluster["members"] not in high_members:
            add(cluster, MEDIUM)

    candidates.sort(key=lambda group: (group["confidence"] != HIGH, -group["commits"]))
    return [{key: value for key, value in group.items() if key != "commits"} for group in candidates]


def build_identity_map(commits: List[Dict[str, Any]], groups: List[List[str]]) -> Dict[str, str]:
    """Mapeia o id de cada identidade agrupada para o nome canônico do grupo."""
    counts: Counter = Counter()
    names: Dict[str, str] = {}
    for commit in commits:
        key = identity_id(commit.get("author", ""), commit.get("email", ""))
        counts[key] += 1
        names[key] = commit.get("author", "")

    mapping: Dict[str, str] = {}
    for group in groups:
        members = [member for member in group if member in counts]
        if len(members) < 2:
            continue
        # O nome canônico é o que mais aparece somando as identidades do grupo (empate: o mais longo).
        commits_by_name: Counter = Counter()
        for member in members:
            commits_by_name[names[member]] += counts[member]
        canonical = max(commits_by_name, key=lambda name: (commits_by_name[name], len(name)))
        for member in members:
            mapping[member] = canonical

    return mapping
