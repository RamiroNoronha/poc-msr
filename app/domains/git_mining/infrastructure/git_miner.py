import subprocess
import tempfile
import threading
import time
from typing import List, Optional, Tuple, Dict

GitLogReport = Tuple[List[str], Dict[str, int]]

CACHE_TTL_SECONDS = 600
CACHE_MAX_ENTRIES = 8

# As requisições de uma mesma análise (desenvolvedores, mineração e Truck Factor)
# reaproveitam o mesmo clone/log em vez de clonar o repositório de novo.
_cache: Dict[Tuple[str, Optional[str]], Tuple[float, GitLogReport]] = {}
_cache_lock = threading.Lock()


class NativeGitMiner:

    def generate_gitlog_report(self, repo_url: str, branch: Optional[str] = None) -> GitLogReport:
        key = (repo_url, branch)

        with _cache_lock:
            cached = _cache.get(key)
            if cached and time.monotonic() - cached[0] < CACHE_TTL_SECONDS:
                return cached[1]

            result, succeeded = self._mine_repository(repo_url, branch)

            if succeeded:
                _cache[key] = (time.monotonic(), result)
                while len(_cache) > CACHE_MAX_ENTRIES:
                    del _cache[min(_cache, key=lambda k: _cache[k][0])]

            return result

    def _mine_repository(self, repo_url: str, branch: Optional[str] = None) -> Tuple[GitLogReport, bool]:
        report = []
        file_sizes = {}
        succeeded = False

        with tempfile.TemporaryDirectory(prefix="repo-clone-") as temp_dir:
            try:
                clone_cmd = ['git', 'clone', '--bare', repo_url, temp_dir]
                if branch:

                    clone_cmd = ['git', 'clone', '--bare',
                                 '--branch', branch, repo_url, temp_dir]

                subprocess.run(clone_cmd, check=True, capture_output=True)

                ref = branch if branch else 'HEAD'

                result_log = subprocess.run(
                    ['git', 'log', ref, '--reverse', '--name-only',
                        '--format=COMMIT|%H|%an|%ae|%ad|%s', '--date=iso'],
                    cwd=temp_dir, check=True, capture_output=True, text=True
                )
                report = result_log.stdout.splitlines()

                result_ls = subprocess.run(
                    ['git', 'ls-tree', '--name-only', '-r', ref],
                    cwd=temp_dir, check=True, capture_output=True, text=True
                )
                files = result_ls.stdout.splitlines()

                for file_path in files:
                    try:
                        result_show = subprocess.run(
                            ['git', 'show', f'{ref}:{file_path}'],
                            cwd=temp_dir, capture_output=True, check=True
                        )

                        lines_of_code = result_show.stdout.count(b'\n')

                        file_sizes[file_path] = lines_of_code

                    except subprocess.CalledProcessError:
                        continue

                succeeded = True

            except subprocess.CalledProcessError as e:
                print(f"Error executing git command: {e.stderr}")

        return (report, file_sizes), succeeded
