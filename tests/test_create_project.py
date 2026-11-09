"""The all-or-nothing invariant of create_project.sh, exercised with a fake `gh`.

Invariant: a project repository never stays reachable without its guardrails. If a step
fails after the repository exists, the script must archive it and exit non-zero; if it
fails before, it must not touch anything.
"""
import os
import pathlib
import stat
import subprocess
import tempfile
import textwrap
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
IDEA = textwrap.dedent("""\
    ---
    name: spot-price-tracker
    visibility: public
    cloud: none
    monthly_cap_usd: 0
    ---

    ## Problem
    GPU spot prices swing by region and hour; nobody watches them.

    ## Smallest useful version
    A page showing today's cheapest region for one instance type.

    ## How we'll know it works
    The page's price matches the public pricing data within one refresh.

    ## Cost
    $0: GitHub Pages plus a scheduled Action reading public data.

    ## Kill criteria
    If the data needs credentials to read, stop and archive.
    """)

# A fake gh: logs every call; fails the call whose arguments contain $FAIL_ON.
FAKE_GH = textwrap.dedent("""\
    #!/usr/bin/env bash
    echo "$*" >> "$GH_LOG"
    if [ -n "${FAIL_ON:-}" ] && [[ "$*" == *"$FAIL_ON"* ]]; then
      echo "simulated failure" >&2; exit 1
    fi
    case "$*" in *--jq\\ .id*) echo 42 ;; esac
    """)


class CreateProjectAllOrNothing(unittest.TestCase):
    def run_script(self, fail_on: str) -> tuple[int, list[str]]:
        with tempfile.TemporaryDirectory() as d:
            d = pathlib.Path(d)
            (d / "bin").mkdir()
            gh = d / "bin" / "gh"
            gh.write_text(FAKE_GH)
            gh.chmod(gh.stat().st_mode | stat.S_IEXEC)
            log = d / "gh.log"
            log.touch()
            idea = ROOT / "ideas" / "spot-price-tracker.md"
            idea.write_text(IDEA)
            try:
                env = dict(os.environ, PATH=f"{d / 'bin'}:{os.environ['PATH']}",
                           GH_LOG=str(log), FAIL_ON=fail_on, OWNER="labs",
                           APPROVER="someone", GH_TOKEN="fake", FACTORY_REPO="me/factory",
                           APP_SLUG="factory-provisioner")
                r = subprocess.run(["bash", str(ROOT / "scripts" / "create_project.sh"),
                                    str(idea)], env=env, capture_output=True, text=True)
            finally:
                idea.unlink()
            return r.returncode, log.read_text().splitlines()

    def test_failure_after_creation_archives_the_repo(self):
        # The bot-id lookup happens after the repo exists and before any git push.
        code, calls = self.run_script(fail_on="%5Bbot%5D")
        self.assertNotEqual(code, 0)
        self.assertTrue(any(c.startswith("api -X POST orgs/labs/repos") for c in calls), calls)
        self.assertIn("api -X PATCH repos/labs/spot-price-tracker -F archived=true --silent",
                      calls)

    def test_failure_before_creation_touches_nothing(self):
        code, calls = self.run_script(fail_on="orgs/labs/repos")
        self.assertNotEqual(code, 0)
        self.assertFalse(any("archived=true" in c for c in calls), calls)


if __name__ == "__main__":
    unittest.main()
