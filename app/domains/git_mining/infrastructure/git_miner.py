import subprocess
import tempfile
from typing import List


class NativeGitMiner:

    def generate_gitlog_report(self, repo_url: str) -> List[str]:
        report = []
        with tempfile.TemporaryDirectory(prefix="repo-clone-") as temp_dir:
            try:
                subprocess.run(['git', 'clone', '--bare', repo_url,
                               temp_dir], check=True, capture_output=True)
                result = subprocess.run(
                    ['git', 'log', '--name-only',
                        '--format=COMMIT|%H|%an|%ad|%s', '--date=iso'],
                    cwd=temp_dir, check=True, capture_output=True, text=True
                )
                report = result.stdout.splitlines()
            except subprocess.CalledProcessError as e:
                print(f"Error executing git command: {e.stderr}")

        return report
