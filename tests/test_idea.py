import pathlib
import sys
import tempfile
import textwrap
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "scripts"))
import idea  # noqa: E402

CFG = {"account_monthly_cap_usd": 30, "private_allowed": False,
       "reserved_names": ["factory"]}
BODY = """## Problem
GPU spot prices swing by region and hour; nobody watches them for me.

## Smallest useful version
A page that shows today's cheapest region for g6.2xlarge, refreshed hourly.

## How we'll know it works
The page's price matches the AWS pricing API within one refresh, checked in CI.

## Cost
$0: GitHub Pages plus a scheduled Action reading public price data.

## Kill criteria
If AWS data cannot be read without credentials, stop and archive.
"""


def write(dirpath: pathlib.Path, filename: str, front: str, body: str = BODY) -> pathlib.Path:
    ideas = dirpath / "ideas"
    ideas.mkdir(exist_ok=True)
    p = ideas / filename
    p.write_text(f"---\n{textwrap.dedent(front).strip()}\n---\n\n{body}\n")
    return p


GOOD = """
name: spot-price-tracker   # the repo name
visibility: public
cloud: none
monthly_cap_usd: 0
"""


class ValidateIdea(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = pathlib.Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def errors(self, front, filename="spot-price-tracker.md", body=BODY):
        return idea.validate(write(self.dir, filename, front, body), CFG)

    def test_valid_idea_passes(self):
        self.assertEqual(self.errors(GOOD), [])

    def test_aws_idea_within_cap_passes(self):
        front = GOOD.replace("cloud: none", "cloud: aws").replace("_usd: 0", "_usd: 5")
        self.assertEqual(self.errors(front), [])

    def test_bad_names_rejected(self):
        for bad in ("Spot", "a", "-spot", "spot-", "sp--ot", "spot_price", "x" * 41,
                    "spot;rm -rf", "$(id)"):
            with self.subTest(name=bad):
                errs = self.errors(GOOD.replace("spot-price-tracker", bad))
                self.assertTrue(any("name" in e for e in errs), errs)

    def test_reserved_name_rejected(self):
        errs = self.errors(GOOD.replace("spot-price-tracker", "factory"), "factory.md")
        self.assertTrue(any("reserved" in e for e in errs), errs)

    def test_file_name_must_match(self):
        errs = self.errors(GOOD, "other-name.md")
        self.assertTrue(any("ideas/spot-price-tracker.md" in e for e in errs), errs)

    def test_private_rejected_without_guardrails(self):
        errs = self.errors(GOOD.replace("public", "private"))
        self.assertTrue(any("never private without guardrails" in e for e in errs), errs)

    def test_cap_over_account_cap_rejected(self):
        front = GOOD.replace("cloud: none", "cloud: aws").replace("_usd: 0", "_usd: 31")
        self.assertTrue(any("exceeds the account cap" in e for e in self.errors(front)))

    def test_no_cloud_means_zero_cap(self):
        errs = self.errors(GOOD.replace("_usd: 0", "_usd: 5"))
        self.assertTrue(any("cloud: none means" in e for e in errs), errs)

    def test_non_integer_cap_rejected(self):
        for bad in ("5.5", "-1", "five", "1e3"):
            with self.subTest(cap=bad):
                errs = self.errors(GOOD.replace("_usd: 0", f"_usd: {bad}"))
                self.assertTrue(any("whole number" in e for e in errs), errs)

    def test_unknown_and_missing_keys_rejected(self):
        errs = self.errors(GOOD.replace("cloud: none", "run: make up"))
        self.assertTrue(any("unknown keys: run" in e for e in errs), errs)
        self.assertTrue(any("missing keys: cloud" in e for e in errs), errs)

    def test_duplicate_and_nested_keys_rejected(self):
        self.assertTrue(any("duplicate" in e for e in self.errors(GOOD + "\nname: other")))
        self.assertTrue(any("nested" in e for e in self.errors(GOOD + "\n  sub: x")))

    def test_missing_section_rejected(self):
        body = BODY.replace("## Kill criteria", "## Notes")
        self.assertTrue(any("missing section '## Kill criteria'" in e
                            for e in self.errors(GOOD, body=body)))

    def test_empty_section_rejected(self):
        body = BODY.replace("Kill criteria\nIf AWS data cannot be read without credentials, "
                            "stop and archive.", "Kill criteria\ntbd")
        self.assertTrue(any("is empty" in e for e in self.errors(GOOD, body=body)))

    def test_section_headings_case_insensitive(self):
        self.assertEqual(self.errors(GOOD, body=BODY.replace("## Cost", "## COST")), [])

    def test_missing_front_matter_rejected(self):
        p = self.dir / "ideas"
        p.mkdir()
        f = p / "x.md"
        f.write_text("no front matter here\n")
        self.assertTrue(any("front-matter" in e for e in idea.validate(f, CFG)))

    def test_readme_and_templates_are_not_ideas(self):
        # Regression: CI once validated ideas/README.md and _template.md as ideas, and
        # `changed` would have tried to create a repository named README on merge.
        self.assertFalse(idea.is_idea(pathlib.Path("ideas/README.md")))
        self.assertFalse(idea.is_idea(pathlib.Path("ideas/_template.md")))
        self.assertFalse(idea.is_idea(pathlib.Path("docs/spot.md")))
        self.assertTrue(idea.is_idea(pathlib.Path("ideas/spot-price-tracker.md")))

    def test_underscore_files_are_templates(self):
        errs = self.errors(GOOD, "_template.md")
        self.assertTrue(any("templates" in e for e in errs), errs)


if __name__ == "__main__":
    unittest.main()
