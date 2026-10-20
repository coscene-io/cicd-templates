"""Verify optional runtime packaging and its credential/shell boundaries."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

import yaml

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = yaml.load((ROOT / ".github/workflows/image-push-pnpm.yml").read_text(), Loader=yaml.BaseLoader)


class PnpmPackageTests(unittest.TestCase):
    def test_optional_package_preserves_build_credential_boundary(self):
        inputs = WORKFLOW["on"]["workflow_call"]["inputs"]
        self.assertEqual(inputs["package"]["default"], "")
        self.assertEqual(inputs["package"]["required"], "false")
        steps = WORKFLOW["jobs"]["build"]["steps"]
        by_name = {s["name"]: s for s in steps}
        setup = by_name["Setup Node, pnpm and dependencies"]
        build = by_name["Build"]
        package = by_name["Package runtime"]
        self.assertEqual(setup["if"], "${{ inputs.build != '' || inputs.package != '' }}")
        self.assertEqual(setup["with"]["install"], "true")
        self.assertEqual(package["if"], "${{ inputs.package != '' }}")
        self.assertNotIn("PNPM_CONFIG__AUTH", build["env"])
        self.assertNotIn("PNPM_CONFIG__AUTH", WORKFLOW["jobs"]["build"]["env"])
        self.assertEqual(package["env"]["PNPM_CONFIG__AUTH"], setup["env"]["PNPM_CONFIG__AUTH"])
        self.assertLess(steps.index(build), steps.index(package))
        self.assertLess(steps.index(package), steps.index(by_name["Docker build & push"]))

    def test_script_name_is_passed_as_one_literal_argument(self):
        step = next(s for s in WORKFLOW["jobs"]["build"]["steps"] if s["name"] == "Package runtime")
        self.assertEqual(step["env"]["PACKAGE_SCRIPT"], "${{ inputs.package }}")
        self.assertNotIn("${{", step["run"])
        for script in ("gidle:package:release", "package $(touch injected); echo bad"):
            with self.subTest(script=script), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                executable = root / "pnpm"
                executable.write_text("#!/usr/bin/env python3\n"
                    "import json,os,sys\n"
                    "with open(os.environ['CALLS'], 'w') as f: json.dump(sys.argv[1:],f)\n")
                executable.chmod(0o755)
                env = {**os.environ, "PATH": str(root) + os.pathsep + os.environ["PATH"],
                       "PACKAGE_SCRIPT": script, "MEASURE_RESOURCES": "false", "CALLS": str(root / "calls.json")}
                subprocess.run(["bash", "-c", step["run"]], cwd=root, env=env, check=True)
                self.assertEqual(json.loads((root / "calls.json").read_text()), ["run", script])
                self.assertFalse((root / "injected").exists())


if __name__ == "__main__":
    unittest.main()
