"""Execute the actual workflow shell with a recording Skaffold substitute."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

import yaml

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = yaml.load((ROOT / ".github/workflows/image-push-go.yml").read_text(), Loader=yaml.BaseLoader)


class SkaffoldFileTests(unittest.TestCase):
    def test_optional_default_and_quoted_override_reach_every_build(self):
        inputs = WORKFLOW["on"]["workflow_call"]["inputs"]
        self.assertEqual(inputs["skaffold-file"], {
            "description": "Skaffold config path relative to workspace",
            "required": "false", "type": "string", "default": "skaffold.yaml"})
        step = next(s for s in WORKFLOW["jobs"]["build"]["steps"] if s.get("id") == "build-and-push")
        self.assertEqual(step["env"]["SKAFFOLD_FILE"], "${{ inputs.skaffold-file }}")
        self.assertEqual(step["env"]["BUILD_WORKSPACE"], "${{ inputs.workspace }}")
        for event in ("push", "release", "prerelease"):
            for config in (inputs["skaffold-file"]["default"], "configs/GPU build $(touch injected).yaml"):
                with self.subTest(event=event, config=config), tempfile.TemporaryDirectory() as directory:
                    root = Path(directory)
                    workspace = root / "workspace with spaces"
                    workspace.mkdir()
                    executable = root / "skaffold"
                    executable.write_text("#!/usr/bin/env python3\n"
                        "import json,os,sys\n"
                        "with open(os.environ['CALLS'], 'a') as f: f.write(json.dumps({'args':sys.argv[1:],'cwd':os.getcwd()})+'\\n')\n"
                        "print(json.dumps({'builds':[{'tag':'registry/test:resolved@sha256:abc'}]}))\n")
                    executable.chmod(0o755)
                    script = step["run"].replace("${{ github.event_name }}", event)
                    env = {**os.environ, "PATH": str(root) + os.pathsep + os.environ["PATH"],
                           "BUILD_WORKSPACE": str(workspace), "SKAFFOLD_FILE": config,
                           "IMAGE_TAG": "commit-sha", "CALLS": str(root / "calls.jsonl"),
                           "GITHUB_OUTPUT": str(root / "outputs")}
                    subprocess.run(["bash", "-e", "-o", "pipefail", "-c", script],
                                   env=env, check=True, capture_output=True, text=True)
                    calls = [json.loads(line) for line in (root / "calls.jsonl").read_text().splitlines()]
                    self.assertEqual(len(calls), 1 if event == "push" else 2)
                    for call in calls:
                        self.assertEqual(call["args"][:3], ["build", "-f", config])
                        self.assertEqual(call["cwd"], str(workspace))
                    self.assertEqual(calls[0]["args"][-2:], ["-t", "commit-sha"])
                    self.assertFalse((workspace / "injected").exists())


if __name__ == "__main__":
    unittest.main()
