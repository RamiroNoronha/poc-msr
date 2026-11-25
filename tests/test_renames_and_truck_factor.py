"""Testes da resolução de renomeações e do filtro de arquivos do Truck Factor.

Rodar com: .venv/bin/python -m unittest discover -s tests
"""
import unittest

from app.domains.git_mining.renames import parse_name_status, resolve_renames
from app.domains.git_mining.service import GitMiningService
from app.domains.truck_factor.service import TruckFactorService


class FakeMiner:
    def __init__(self, log_lines, file_sizes):
        self.log_lines = log_lines
        self.file_sizes = file_sizes

    def generate_gitlog_report(self, repo_url, branch=None):
        return self.log_lines, self.file_sizes


def commit(author, *changes):
    return [f"COMMIT|{author}-hash|{author}|{author.lower()}@x.com|2026-01-01 10:00:00 +0000|msg", *changes]


class ParseNameStatusTest(unittest.TestCase):
    def test_modified(self):
        self.assertEqual(parse_name_status("M\tsrc/a.py"), ("M", None, "src/a.py"))

    def test_rename_with_similarity(self):
        self.assertEqual(parse_name_status("R087\tsrc/a.py\tpkg/a.py"), ("R", "src/a.py", "pkg/a.py"))

    def test_invalid_line(self):
        self.assertIsNone(parse_name_status("sem tab"))


class ResolveRenamesTest(unittest.TestCase):
    def test_history_of_old_path_goes_to_current_path(self):
        resolved = resolve_renames([
            [("A", None, "src/a.py")],
            [("M", None, "src/a.py")],
            [("R", "src/a.py", "pkg/a.py")],
            [("M", None, "pkg/a.py")],
        ])
        self.assertEqual(resolved, [["pkg/a.py"]] * 4)

    def test_rename_chain(self):
        resolved = resolve_renames([
            [("A", None, "a")],
            [("R", "a", "b")],
            [("R", "b", "c")],
        ])
        self.assertEqual(resolved, [["c"], ["c"], ["c"]])

    def test_reused_path_is_a_different_file(self):
        # "a" vira "b"; depois nasce um arquivo novo chamado "a".
        resolved = resolve_renames([
            [("A", None, "a")],
            [("R", "a", "b")],
            [("A", None, "a")],
            [("M", None, "a")],
        ])
        self.assertEqual(resolved, [["b"], ["b"], ["a"], ["a"]])

    def test_deleted_file_keeps_its_name(self):
        resolved = resolve_renames([[("A", None, "old")], [("D", None, "old")]])
        self.assertEqual(resolved, [["old"], ["old"]])


class GitMiningRenamesTest(unittest.TestCase):
    def test_process_gitlog_follows_renames(self):
        log = [
            *commit("Ana", "A\tsrc/core.py"),
            *commit("Ana", "M\tsrc/core.py"),
            *commit("Bia", "R100\tsrc/core.py\tpackages/core.py"),
        ]
        service = GitMiningService(FakeMiner(log, {"packages/core.py": 50}))
        commits, _ = service.process_gitlog("repo")
        self.assertEqual([c["files_touched"] for c in commits], [["packages/core.py"]] * 3)


class TruckFactorTest(unittest.TestCase):
    def build(self, log, sizes):
        return TruckFactorService(GitMiningService(FakeMiner(log, sizes)))

    def test_creator_keeps_authorship_after_folder_move(self):
        # Ana cria e mantém o arquivo; Bia só move a pasta. Sem seguir renomeações, Bia seria a "criadora".
        log = [
            *commit("Ana", "A\tsrc/core.py"),
            *commit("Ana", "M\tsrc/core.py"),
            *commit("Ana", "M\tsrc/core.py"),
            *commit("Bia", "R100\tsrc/core.py\tpackages/core.py"),
        ]
        report = self.build(log, {"packages/core.py": 50}).get_truck_factor_report("repo")
        self.assertEqual(report["key_developers"], ["Ana"])
        self.assertEqual(report["total_files_analyzed"], 1)

    def test_deleted_files_are_ignored(self):
        log = [*commit("Ana", "A\tkeep.py"), *commit("Bia", "A\tgone.py"), *commit("Bia", "D\tgone.py")]
        report = self.build(log, {"keep.py": 10}).get_truck_factor_report("repo")
        self.assertEqual(report["total_files_analyzed"], 1)
        self.assertEqual(report["key_developers"], ["Ana"])

    def test_excluded_folders_are_ignored(self):
        log = [
            *commit("Ana", "A\tpackages/a.py"),
            *commit("Bia", "A\texamples/x.ts"),
            *commit("Bia", "A\texamples/y.ts"),
            *commit("Bia", "A\texamples-extra/z.ts"),
        ]
        sizes = {"packages/a.py": 1, "examples/x.ts": 1, "examples/y.ts": 1, "examples-extra/z.ts": 1}
        service = self.build(log, sizes)

        self.assertEqual(service.get_truck_factor_report("repo")["total_files_analyzed"], 4)

        report = service.get_truck_factor_report("repo", excluded_paths=["examples/"])
        # "examples-extra" não é a pasta "examples": continua na conta.
        self.assertEqual(report["total_files_analyzed"], 2)


if __name__ == "__main__":
    unittest.main()
