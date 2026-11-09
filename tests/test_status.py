import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "scripts"))
import status  # noqa: E402

PROJECT = {"name": "sky-hoppers", "url": "https://github.com/labs/sky-hoppers",
           "play": "https://labs.github.io/sky-hoppers/", "description": "A platformer",
           "stage": "experiment", "ci": "success",
           "ci_url": "https://github.com/labs/sky-hoppers/actions/runs/1", "pushed": "2026-11-09"}


class RenderStatus(unittest.TestCase):
    def test_lists_project_with_play_link_and_ci(self):
        page = status.render("labs", [PROJECT], "2026-11-09 08:00")
        self.assertIn('href="https://labs.github.io/sky-hoppers/">▶ play', page)
        self.assertIn(">success</a>", page)
        self.assertIn(">sky-hoppers</a>", page)

    def test_empty_org_says_so(self):
        self.assertIn("No projects yet.", status.render("labs", [], "now"))

    def test_agent_editable_text_is_escaped(self):
        # Descriptions and links live in repos agents can edit; none may become markup.
        evil = dict(PROJECT, description='<script>alert(1)</script>',
                    name='x"><img src=x onerror=alert(1)>', stage='a" onmouseover="x')
        page = status.render("labs", [evil], "now")
        self.assertNotIn("<script>", page)
        self.assertNotIn("<img", page)
        self.assertNotIn('" onmouseover="', page)

    def test_only_https_links_are_linked(self):
        page = status.render("labs", [dict(PROJECT, play="javascript:alert(1)")], "now")
        self.assertNotIn('href="javascript:', page)


if __name__ == "__main__":
    unittest.main()
