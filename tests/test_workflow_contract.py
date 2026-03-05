import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS_DIR = ROOT / ".github" / "workflows"


class WorkflowContractTests(unittest.TestCase):
    TASK_EXPECTATIONS = {
        "ci.yml": "run: mise run ci",
        "deploy.yml": "run: mise run deploy",
        "prettier.yml": "run: mise run format:write",
        "standard.yml": "run: mise run lint:ruby",
        "erb-lint.yml": "run: mise run lint:erb",
        "brakeman.yml": "run: mise run security",
    }

    def test_all_workflows_use_mise_action_v3(self):
        for workflow_name in self.TASK_EXPECTATIONS:
            content = (WORKFLOWS_DIR / workflow_name).read_text()
            self.assertIn("uses: jdx/mise-action@v3", content, workflow_name)

    def test_all_workflows_enable_mise_experimental(self):
        for workflow_name in self.TASK_EXPECTATIONS:
            content = (WORKFLOWS_DIR / workflow_name).read_text()
            self.assertIn("MISE_EXPERIMENTAL: true", content, workflow_name)

    def test_all_workflows_removed_standalone_mise_install(self):
        for workflow_name in self.TASK_EXPECTATIONS:
            content = (WORKFLOWS_DIR / workflow_name).read_text()
            self.assertNotIn("run: mise install", content, workflow_name)

    def test_all_workflows_run_expected_task(self):
        for workflow_name, expected_task_line in self.TASK_EXPECTATIONS.items():
            content = (WORKFLOWS_DIR / workflow_name).read_text()
            self.assertIn(expected_task_line, content, workflow_name)


class ReadmeContractTests(unittest.TestCase):
    def test_readme_documents_required_tasks(self):
        content = (ROOT / "README.md").read_text()
        self.assertIn("Required tasks:", content)
        for task in ["setup", "ci", "test", "lint", "build", "dev"]:
            self.assertIn(f"- `{task}`", content)

    def test_readme_documents_optional_tasks(self):
        content = (ROOT / "README.md").read_text()
        for task in ["deploy", "security", "format", "format:write"]:
            self.assertIn(f"- `{task}`", content)

    def test_readme_includes_framework_examples_and_placeholders(self):
        content = (ROOT / "README.md").read_text()
        self.assertIn("### Rails `mise.toml` example", content)
        self.assertIn("### Nuxt `mise.toml` example", content)
        self.assertIn("### Next.js `mise.toml` example", content)
        self.assertIn("# TODO: choose rubocop/standardrb command", content)
        self.assertIn("# TODO: choose your Nuxt deployment command", content)
        self.assertIn("# TODO: choose your Next.js deployment command", content)


if __name__ == "__main__":
    unittest.main()
