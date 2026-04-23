import subprocess
import tempfile
from typing import List, Tuple, Dict


class NativeGitMiner:

    def generate_gitlog_report(self, repo_url: str) -> Tuple[List[str], Dict[str, int]]:
        report = []
        file_sizes = {}

        with tempfile.TemporaryDirectory(prefix="repo-clone-") as temp_dir:
            try:
                subprocess.run(['git', 'clone', '--bare', repo_url, temp_dir],
                               check=True, capture_output=True)

                result_log = subprocess.run(
                    ['git', 'log', '--name-only',
                        '--format=COMMIT|%H|%an|%ad|%s', '--date=iso'],
                    cwd=temp_dir, check=True, capture_output=True, text=True
                )
                report = result_log.stdout.splitlines()

                result_ls = subprocess.run(
                    ['git', 'ls-tree', '--name-only', '-r', 'HEAD'],
                    cwd=temp_dir, check=True, capture_output=True, text=True
                )
                files = result_ls.stdout.splitlines()

                for file_path in files:
                    try:
                        result_show = subprocess.run(
                            ['git', 'show', f'HEAD:{file_path}'],
                            cwd=temp_dir, capture_output=True, check=True
                        )

                        lines_of_code = result_show.stdout.count(b'\n')

                        file_sizes[file_path] = lines_of_code

                    except subprocess.CalledProcessError:
                        continue

            except subprocess.CalledProcessError as e:
                print(f"Error executing git command: {e.stderr}")

        return report, file_sizes
