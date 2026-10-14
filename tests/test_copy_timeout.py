"""Check the timeout contract across both reusable workflows."""
from pathlib import Path
import unittest
import yaml

ROOT = Path(__file__).resolve().parents[1] / ".github/workflows"

class CopyTimeoutTests(unittest.TestCase):
    def test_default_and_forwarding(self):
        build = yaml.load((ROOT / "image-push-go.yml").read_text(), Loader=yaml.BaseLoader)
        copy = yaml.load((ROOT / "cp-image-to-volcengine.yml").read_text(), Loader=yaml.BaseLoader)
        for workflow, name in ((build, "copy-timeout-minutes"), (copy, "timeout-minutes")):
            setting = workflow["on"]["workflow_call"]["inputs"][name]
            self.assertEqual(setting["default"], "15")
            self.assertEqual(setting["type"], "number")
            self.assertEqual(setting["required"], "false")
        self.assertEqual(build["jobs"]["cp-image-to-volcengine"]["with"]["timeout-minutes"],
                         "${{ inputs.copy-timeout-minutes }}")
        self.assertEqual(copy["jobs"]["cp-image-use-gh"]["timeout-minutes"],
                         "${{ inputs.timeout-minutes }}")
