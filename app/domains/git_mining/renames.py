"""Segue renomeações: o histórico de um caminho antigo passa a contar para o caminho atual do arquivo.

Cada commit chega com as mudanças do `git log --name-status -M` na forma (status, caminho_antigo, caminho_novo),
do commit mais antigo para o mais recente. A resolução percorre o histórico de trás para frente, mantendo um
apelido "caminho naquela época -> caminho final". Assim, um caminho reaproveitado depois (A renomeado para B e,
mais tarde, um arquivo novo criado como A) não mistura a história dos dois arquivos.
"""
from typing import Dict, List, Optional, Tuple

Change = Tuple[str, Optional[str], str]


def parse_name_status(line: str) -> Optional[Change]:
    """Converte uma linha do `--name-status` (ex.: "M\\tpath", "R087\\told\\tnew") em (status, antigo, novo)."""
    parts = line.split("\t")
    if len(parts) < 2 or not parts[0]:
        return None

    status = parts[0][0]
    if status in ("R", "C") and len(parts) >= 3:
        return status, parts[1], parts[2]
    return status, None, parts[-1]


def resolve_renames(commits_changes: List[List[Change]]) -> List[List[str]]:
    """Para cada commit (do mais antigo ao mais recente), devolve os caminhos tocados já com o nome final."""
    alias: Dict[str, str] = {}
    resolved: List[List[str]] = [[] for _ in commits_changes]

    for index in range(len(commits_changes) - 1, -1, -1):
        touched: List[str] = []
        for status, old_path, new_path in commits_changes[index]:
            final_path = alias.get(new_path, new_path)
            touched.append(final_path)

            if status == "R" and old_path:
                # Antes deste commit o arquivo se chamava `old_path`; `new_path` ainda não era este arquivo.
                alias.pop(new_path, None)
                alias[old_path] = final_path
            elif status in ("A", "C"):
                # O arquivo nasceu aqui: um caminho igual em commits anteriores é outro arquivo.
                alias.pop(new_path, None)

        resolved[index] = list(dict.fromkeys(touched))

    return resolved
