import subprocess
import tempfile
from typing import List, Optional, Tuple, Dict


class NativeGitMiner:

    def generate_gitlog_report(self, repo_url: str, branch: Optional[str] = None) -> Tuple[List[str], Dict[str, int]]:
        report = []
        file_sizes = {}

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
                        '--format=COMMIT|%H|%an|%ad|%s', '--date=iso'],
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

            except subprocess.CalledProcessError as e:
                print(f"Error executing git command: {e.stderr}")

        return report, file_sizes
