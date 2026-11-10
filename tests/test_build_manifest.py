import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

from foundation_template import __version__
from foundation_template_bridge.schemas import tool_definitions

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "SOURCE-MANIFEST.json"


def canonical():
    return json.dumps(tool_definitions(), ensure_ascii=True, allow_nan=False, sort_keys=True,
                      separators=(",", ":")).encode("ascii")


class ManifestToolTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.copy = Path(self.temp.name)
        for name in [*json.loads(MANIFEST.read_text())["files"], MANIFEST.name]:
            (self.copy / name).parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / name, self.copy / name)

    def build(self, *argv):
        proc = subprocess.run([sys.executable, "-B", "tools/build_manifest.py", *argv], cwd=self.copy,
                              capture_output=True, timeout=60)
        self.assertEqual((proc.returncode, proc.stderr), (0, b""))
        return proc.stdout

    def test_gap_tpl_006_inventory_and_manifest_summary(self):
        before = (self.copy / MANIFEST.name).read_bytes()
        self.assertEqual(self.build("--inventory"), canonical() + b"\n")
        self.assertEqual((self.copy / MANIFEST.name).read_bytes(), before)
        summary = json.loads(self.build())
        written = (self.copy / MANIFEST.name).read_bytes()
        self.assertEqual(set(summary), {"files", "sha256", "inventory_sha256"})
        self.assertEqual(summary["files"], len(json.loads(written)["files"]))
        self.assertEqual(summary["files"], len(json.loads(before)["files"]))
        self.assertEqual(summary["sha256"], hashlib.sha256(written).hexdigest())
        self.assertEqual(written, MANIFEST.read_bytes())
        self.assertEqual(summary["inventory_sha256"], hashlib.sha256(canonical()).hexdigest())

    def test_f7_manifest_version_follows_package_version(self):
        self.assertEqual(json.loads(MANIFEST.read_text())["version"], __version__)
        (self.copy / "foundation_template/__init__.py").write_text('__version__ = "9.8.7"\n')
        self.build()
        self.assertEqual(json.loads((self.copy / MANIFEST.name).read_text())["version"], "9.8.7")


if __name__ == "__main__":
    unittest.main()
