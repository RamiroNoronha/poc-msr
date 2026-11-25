import os
import unittest

os.environ.setdefault("GITHUB_TOKEN", "test")

from app.domains.git_mining.repository_guard import RepositoryRejected, parse_github_url  # noqa: E402


class ParseGithubUrlTest(unittest.TestCase):
    def test_accepts_github_urls(self):
        self.assertEqual(parse_github_url("https://github.com/TanStack/query"), ("TanStack", "query"))
        self.assertEqual(parse_github_url("https://github.com/encode/httpx.git"), ("encode", "httpx"))
        self.assertEqual(parse_github_url(" https://github.com/date-fns/date-fns/ "), ("date-fns", "date-fns"))

    def test_rejects_other_hosts_and_schemes(self):
        for url in [
            "http://github.com/a/b",
            "https://gitlab.com/a/b",
            "https://github.com.evil.com/a/b",
            "file:///etc/passwd",
            "/tmp/repo",
            "--upload-pack=touch /tmp/x",
            "https://github.com/a/b/c",
            "https://github.com/a/..",
            "https://user@github.com/a/b",
        ]:
            with self.subTest(url=url), self.assertRaises(RepositoryRejected):
                parse_github_url(url)


if __name__ == "__main__":
    unittest.main()
