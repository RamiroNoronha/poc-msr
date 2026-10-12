"""Acoplamento lógico (change coupling): arquivos que costumam mudar juntos nos mesmos commits."""
import fnmatch
import itertools
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from app.domains.git_mining.service import GitMiningService

# Commits com mais arquivos que isto são pulados só por desempenho (N arquivos geram N*(N-1)/2 pares).
MAX_COMMIT_FILES = 200
DAYS_PER_MONTH = 30.44

# Arquivos que mudam em quase todo release/commit e só geram ruído no acoplamento.
NOISE_NAME_PATTERNS = (
    "package.json", "package-lock.json", "yarn.lock", "pnpm-lock.yaml", "bower.json",
    "composer.json", "composer.lock", "Gemfile.lock", "Cargo.lock", "poetry.lock",
    "go.sum", "CHANGELOG*", "HISTORY*", "*.min.js", "*.min.css", "*.map",
)
NOISE_PATH_PREFIXES = ("dist/", "build/", "node_modules/", "vendor/")


class CouplingService:
    def __init__(self, git_mining_service: GitMiningService):
        self.git_mining_service = git_mining_service

    @staticmethod
    def _parse_date(value: str) -> Optional[datetime]:
        try:
            return datetime.strptime(value.strip(), "%Y-%m-%d %H:%M:%S %z")
        except ValueError:
            return None

    @staticmethod
    def _is_noise(path: str) -> bool:
        name = path.rsplit("/", 1)[-1]
        return path.startswith(NOISE_PATH_PREFIXES) or any(
            fnmatch.fnmatch(name, pattern) for pattern in NOISE_NAME_PATTERNS)

    def get_coupling_report(
        self,
        repo_url: str,
        branch: Optional[str] = None,
        months: Optional[int] = None,
        min_support: int = 3,
        limit: int = 300
    ) -> Dict[str, Any]:
        commits, file_sizes = self.git_mining_service.process_gitlog(
            repo_url, branch)

        dated = [(self._parse_date(commit["date"]), commit)
                 for commit in commits]
        known_dates = [date for date, _ in dated if date]
        latest = max(known_dates) if known_dates else None
        # A janela conta a partir do commit mais recente, e não de hoje.
        cutoff = latest - timedelta(days=months *
                                    DAYS_PER_MONTH) if months and latest else None

        revisions: Counter = Counter()
        pair_commits: Counter = Counter()
        pair_weight: Dict[Tuple[str, str], float] = defaultdict(float)
        analyzed = skipped = 0

        for date, commit in dated:
            if cutoff and date and date < cutoff:
                continue

            files = sorted({path for path in commit["files_touched"]
                            if not self._is_noise(path)})
            if not files:
                continue
            if len(files) > MAX_COMMIT_FILES:
                skipped += 1
                continue

            analyzed += 1
            revisions.update(files)
            if len(files) < 2:
                continue

            # Commits grandes (inclusive squash) contam, mas com peso menor por par.
            weight = 1 / (len(files) - 1)
            for pair in itertools.combinations(files, 2):
                pair_commits[pair] += 1
                pair_weight[pair] += weight

        links = []
        for (source, target), shared in pair_commits.items():
            if shared < min_support:
                continue
            average_revisions = (revisions[source] + revisions[target]) / 2
            links.append({
                "source": source,
                "target": target,
                "commits": shared,
                "weight": round(pair_weight[(source, target)], 4),
                # Grau simétrico: suporte ponderado / média das revisões dos dois arquivos.
                "degree": round(pair_weight[(source, target)] / average_revisions, 4),
                # Confiança direcional: "quando um muda, o outro muda junto em X% das vezes".
                "source_confidence": round(shared / revisions[source], 4),
                "target_confidence": round(shared / revisions[target], 4),
            })

        links.sort(key=lambda link: (-link["degree"], -link["commits"],
                                     link["source"], link["target"]))
        links = links[:limit]

        paths = sorted({link[side] for link in links for side in ("source", "target")})
        files = [
            {"path": path, "revisions": revisions[path], "size": file_sizes.get(path)}
            for path in paths
        ]

        return {
            "window": {
                "months": months,
                "from": cutoff.isoformat() if cutoff else None,
                "to": latest.isoformat() if latest else None,
            },
            "parameters": {"min_support": min_support, "max_commit_files": MAX_COMMIT_FILES},
            "stats": {
                "commits_analyzed": analyzed,
                "commits_skipped_large": skipped,
                "pairs_considered": len(pair_commits),
                "links_returned": len(links),
            },
            "files": files,
            "links": links,
        }
