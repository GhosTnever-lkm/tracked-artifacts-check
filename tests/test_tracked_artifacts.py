import contextlib
import io
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from tracked_artifacts import __version__
from tracked_artifacts.cli import main
from tracked_artifacts.core import classify, scan, tracked_files


class ClassifyTests(unittest.TestCase):
    def test_secret_files(self):
        self.assertEqual(classify(".env").category, "secret-file")
        self.assertEqual(classify("config/.env.production").category, "secret-file")
        self.assertEqual(classify("deploy/server.pem").category, "secret-file")

    def test_common_openssh_private_key_names_are_flagged_but_public_keys_are_not(self):
        for name in ("id_rsa", "id_ecdsa", "id_ed25519", "id_dsa", "id_rsa_sk", "id_ecdsa_sk", "id_ed25519_sk"):
            with self.subTest(name=name):
                self.assertEqual(classify(f".ssh/{name}").category, "secret-file")
        self.assertIsNone(classify(".ssh/id_ed25519.pub"))

    def test_secret_matching_is_case_insensitive_and_portable(self):
        self.assertEqual(classify("CONFIG/.ENV", 10).category, "secret-file")
        self.assertIsNone(classify("CONFIG/.ENV.EXAMPLE", 10))

    def test_example_env_is_allowed(self):
        self.assertIsNone(classify(".env.example"))
        self.assertIsNone(classify("config/.env.sample"))

    def test_dependency_and_build_dirs(self):
        self.assertEqual(classify("node_modules/left-pad/index.js").category, "dependency-dir")
        self.assertEqual(classify("src/__pycache__/x.cpython-313.pyc").category, "build-output")
        self.assertEqual(classify("pkg/mod.pyc").category, "build-output")

    def test_large_file_threshold(self):
        self.assertEqual(classify("data/model.bin", size=6 * 1024 * 1024).category, "large-file")
        self.assertIsNone(classify("data/model.bin", size=1024))

    def test_clean_source_file(self):
        self.assertIsNone(classify("src/app.py", size=2048))


class DocumentationTests(unittest.TestCase):
    def test_readme_ci_example_uses_the_actions_pinned_by_workflows(self):
        root = Path(__file__).resolve().parents[1]
        readme = (root / "README.md").read_text(encoding="utf-8")
        workflow = (root / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
        expected = {
            line.split("#", 1)[0].strip().removeprefix("-").strip()
            for line in workflow.splitlines()
            if "uses: actions/" in line
        }
        for action in expected:
            with self.subTest(action=action):
                self.assertIn(action, readme)

    def test_allow_filters_scan(self):
        found = scan([("docs/key.pem", 1), (".env", 2)], allow=("docs/*",))
        self.assertEqual([f.path for f in found], [".env"])

    def test_allow_globs_use_portable_case_insensitive_matching(self):
        found = scan([("Docs/Fixture.pem", 1)], allow=("docs/*",))
        self.assertEqual(found, [])

    def test_scan_collects_only_matches(self):
        found = scan([("a.py", 10), (".env", 5), ("docs/x.md", 1)])
        self.assertEqual([f.path for f in found], [".env"])


class GitTests(unittest.TestCase):
    def make_repo(self, files: dict[str, bytes]) -> Path:
        root = Path(tempfile.mkdtemp())
        subprocess.run(["git", "init", "-q", str(root)], check=True)
        for name, data in files.items():
            p = root / name
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(data)
        subprocess.run(["git", "-C", str(root), "add", "-A"], check=True)
        return root

    def run_cli(self, argv):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = main(argv)
        return code, buf.getvalue()

    def test_committed_env_fails(self):
        root = self.make_repo({".env": b"TOKEN=1\n", "app.py": b"print(1)\n"})
        code, out = self.run_cli([str(root)])
        self.assertEqual(code, 1)
        self.assertIn(".env", out)

    def test_committed_openssh_private_key_fails_but_public_key_passes(self):
        private_repo = self.make_repo({".ssh/id_ed25519": b"fake test fixture, not a real key\n"})
        code, out = self.run_cli([str(private_repo)])
        self.assertEqual(code, 1)
        self.assertIn(".ssh/id_ed25519", out)

        public_repo = self.make_repo({".ssh/id_ed25519.pub": b"ssh-ed25519 TEST-FIXTURE\n"})
        code, out = self.run_cli([str(public_repo)])
        self.assertEqual(code, 0)
        self.assertIn("no artifacts found", out)

    def test_large_file_uses_index_blob_size_not_working_tree_size(self):
        root = self.make_repo({"payload.bin": b"x" * (6 * 1024 * 1024)})
        (root / "payload.bin").write_bytes(b"x")
        files = tracked_files(root)
        self.assertEqual(files, [("payload.bin", 6 * 1024 * 1024)])
        self.assertEqual(scan(files)[0].category, "large-file")

    def test_working_tree_growth_does_not_change_index_blob_size(self):
        root = self.make_repo({"payload.bin": b"x"})
        (root / "payload.bin").write_bytes(b"x" * (6 * 1024 * 1024))
        files = tracked_files(root)
        self.assertEqual(files, [("payload.bin", 1)])
        self.assertEqual(scan(files), [])

    def test_clean_repo_passes_and_json(self):
        root = self.make_repo({"app.py": b"print(1)\n", ".env.example": b"TOKEN=\n"})
        code, out = self.run_cli(["--json", str(root)])
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out), [])

    def test_allow_glob_suppresses_known_fixture(self):
        root = self.make_repo({"tests/fixtures/key.pem": b"not a real key\n", ".env": b"X=1\n"})
        self.assertEqual(self.run_cli(["--allow", "tests/fixtures/*", str(root)])[0], 1)
        code, out = self.run_cli(["--allow", "tests/fixtures/*", "--json", str(root)])
        self.assertEqual([f["path"] for f in json.loads(out)], [".env"])

    def test_large_threshold_option(self):
        root = self.make_repo({"blob.bin": b"x" * 2048})
        self.assertEqual(self.run_cli(["--large-mb", "0.001", str(root)])[0], 1)
        self.assertEqual(self.run_cli([str(root)])[0], 0)

    def test_tiny_positive_threshold_is_at_least_one_byte(self):
        root = self.make_repo({"one-byte.bin": b"x"})
        self.assertEqual(self.run_cli(["--large-mb", "1e-320", str(root)])[0], 1)

    def test_invalid_large_thresholds_are_rejected(self):
        for value in ("-1", "0", "nan", "inf", "-inf", "1e308"):
            with self.subTest(value=value), contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit) as raised:
                    main(["--large-mb", value])
            self.assertEqual(raised.exception.code, 2)

    def test_version_is_reported_exactly(self):
        with contextlib.redirect_stdout(io.StringIO()) as output:
            with self.assertRaises(SystemExit) as raised:
                main(["--version"])
        self.assertEqual(raised.exception.code, 0)
        self.assertEqual(output.getvalue(), f"{__version__}\n")

    def test_not_a_git_repo_exit_two(self):
        with contextlib.redirect_stderr(io.StringIO()):
            code, _ = self.run_cli([tempfile.mkdtemp()])
        self.assertEqual(code, 2)


if __name__ == "__main__":
    unittest.main()
