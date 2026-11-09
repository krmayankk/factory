import pathlib
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "scripts"))
import check_workflows  # noqa: E402

SHA = "3d3c42e5aac5ba805825da76410c181273ba90b1"
GOOD = f"""name: ci
on: [pull_request]
permissions:
  contents: read
jobs:
  a:
    runs-on: ubuntu-24.04
    steps:
      - uses: actions/checkout@{SHA} # v7.0.1
      - uses: ./local-action
"""


class CheckWorkflows(unittest.TestCase):
    def check(self, text):
        with tempfile.TemporaryDirectory() as d:
            p = pathlib.Path(d) / "wf.yml"
            p.write_text(text)
            return check_workflows.check_file(p)

    def test_good_workflow_passes(self):
        self.assertEqual(self.check(GOOD), [])

    def test_tag_pin_rejected(self):
        errs = self.check(GOOD.replace(f"@{SHA}", "@v7"))
        self.assertTrue(any("not pinned" in e for e in errs), errs)

    def test_short_sha_rejected(self):
        errs = self.check(GOOD.replace(f"@{SHA}", f"@{SHA[:7]}"))
        self.assertTrue(any("not pinned" in e for e in errs), errs)

    def test_pull_request_target_rejected(self):
        errs = self.check(GOOD.replace("[pull_request]", "[pull_request_target]"))
        self.assertTrue(any("pull_request_target" in e for e in errs), errs)

    def test_pull_request_target_as_key_or_list_item_rejected(self):
        for on in ("on:\n  pull_request_target:\n    types: [opened]",
                   "on:\n  - push\n  - pull_request_target",
                   "on: pull_request_target"):
            with self.subTest(on=on):
                errs = self.check(GOOD.replace("on: [pull_request]", on))
                self.assertTrue(any("pull_request_target" in e for e in errs), errs)

    def test_mentioning_pull_request_target_in_a_name_is_fine(self):
        # Regression: the policy step's own name tripped the first version of this check.
        text = GOOD + "      - name: Policy (no pull_request_target)\n        run: true\n"
        self.assertEqual(self.check(text), [])

    def test_missing_permissions_rejected(self):
        errs = self.check(GOOD.replace("permissions:\n  contents: read\n", ""))
        self.assertTrue(any("permissions" in e for e in errs), errs)

    def test_docker_must_be_digest_pinned(self):
        bad = GOOD + "      - uses: docker://alpine:3\n"
        self.assertTrue(any("docker image" in e for e in self.check(bad)))
        good = GOOD + "      - uses: docker://alpine@sha256:" + "a" * 64 + "\n"
        self.assertEqual(self.check(good), [])


if __name__ == "__main__":
    unittest.main()
