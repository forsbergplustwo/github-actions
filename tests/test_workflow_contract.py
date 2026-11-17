import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS_DIR = ROOT / ".github" / "workflows"
ACTIONS_DIR = ROOT / ".github" / "actions"


class WorkflowContractTests(unittest.TestCase):
    WORKFLOWS = {
        "ci-rails.yml": [
            "uses: forsbergplustwo/github-actions/.github/workflows/ci-ruby.yml@",
            "rails: true",
            "app_name: ${{ inputs.app_name }}",
            "master_key: ${{ secrets.master_key }}",
        ],
        "ci-ruby.yml": [
            "uses: $/.github/actions/run-ruby-tests",
            "run: mise run lint:ruby",
            "run: mise run security",
            "run: mise run lint:erb",
            "name: Install",
            "name: Tests",
            "name: RuboCop",
            "name: Brakeman",
            "needs: install",
            "BUNDLE_PATH: ${{ github.workspace }}/vendor/bundle",
            "uses: $/.github/actions/setup-rails",
            "rails:",
            "js: ${{ inputs.rails && inputs.test }}",
            "js: ${{ inputs.rails }}",
            "uses: $/.github/actions/cache-apt",
            "uses: $/.github/actions/commit-autofixes",
        ],
        "ci-js.yml": [
            "run: mise run lint:js",
            "run: mise run test",
            "name: Install",
            "name: Prettier",
            "name: Tests",
            "needs: install",
            "uses: $/.github/actions/setup-mise",
            "uses: $/.github/actions/js-deps",
            "uses: $/.github/actions/commit-autofixes",
        ],
        "deploy.yml": [
            "run: mise run deploy:shopify",
        ],
    }

    def test_expected_workflow_files_exist(self):
        for workflow_name in self.WORKFLOWS:
            self.assertTrue(
                (WORKFLOWS_DIR / workflow_name).exists(),
                workflow_name,
            )
        for removed in ("ci.yml", "standard.yml", "brakeman.yml", "erb-lint.yml", "prettier.yml"):
            self.assertFalse(
                (WORKFLOWS_DIR / removed).exists(),
                f"{removed} should be removed",
            )

    def test_shared_actions_exist(self):
        for action in (
            "setup-rails",
            "run-ruby-tests",
            "cache-apt",
            "commit-autofixes",
            "setup-mise",
            "js-deps",
            "block-pull-request-target",
        ):
            self.assertTrue(
                (ACTIONS_DIR / action / "action.yml").exists(),
                action,
            )
        self.assertFalse(
            (ACTIONS_DIR / "ruby-deps" / "action.yml").exists(),
            "ruby-deps should be folded into setup-rails",
        )

    def test_run_ruby_tests_resolves_mise_tasks_then_fallback(self):
        action = (ACTIONS_DIR / "run-ruby-tests" / "action.yml").read_text()
        self.assertIn("mise tasks info test:ruby", action)
        self.assertIn("mise run test:ruby", action)
        self.assertIn("mise tasks info test", action)
        self.assertIn("mise run test", action)
        self.assertIn("bin/rails test", action)
        self.assertIn("bundle exec rake test", action)

    def test_implementation_workflows_enable_mise_experimental(self):
        for workflow_name in ("ci-ruby.yml", "ci-js.yml", "deploy.yml"):
            content = (WORKFLOWS_DIR / workflow_name).read_text()
            self.assertIn("MISE_EXPERIMENTAL: true", content, workflow_name)
            self.assertLessEqual(
                content.count("MISE_EXPERIMENTAL: true"),
                1,
                f"{workflow_name} should set MISE_EXPERIMENTAL once at workflow level",
            )
        # Thin rails wrapper delegates env to ci-ruby
        rails = (WORKFLOWS_DIR / "ci-rails.yml").read_text()
        self.assertNotIn("MISE_EXPERIMENTAL", rails)

    def test_all_workflows_removed_standalone_mise_install(self):
        for workflow_name in self.WORKFLOWS:
            content = (WORKFLOWS_DIR / workflow_name).read_text()
            self.assertNotIn("run: mise install", content, workflow_name)

    def test_all_workflows_contain_expected_lines(self):
        for workflow_name, expected_lines in self.WORKFLOWS.items():
            content = (WORKFLOWS_DIR / workflow_name).read_text()
            for expected in expected_lines:
                self.assertIn(expected, content, f"{workflow_name}: {expected}")

    def test_ci_ruby_caches_apt_packages_when_rails(self):
        workflow = (WORKFLOWS_DIR / "ci-ruby.yml").read_text()
        action = (ACTIONS_DIR / "cache-apt" / "action.yml").read_text()
        self.assertIn("uses: $/.github/actions/cache-apt", workflow)
        self.assertIn("if: ${{ inputs.rails && inputs.test }}", workflow)
        self.assertIn("path: /var/cache/apt/archives/*.deb", action)
        self.assertIn(
            "key: apt-${{ runner.os }}-${{ hashFiles('**/Aptfile', '**/Aptfile.lock') }}",
            action,
        )

    def test_setup_rails_uses_actions_cache_only(self):
        content = (ACTIONS_DIR / "setup-rails" / "action.yml").read_text()
        self.assertIn("uses: jdx/mise-action@", content)
        self.assertIn("uses: actions/cache@", content)
        self.assertIn(
            "key: bundle-${{ runner.os }}-${{ hashFiles('**/Gemfile.lock', '**/.tool-versions', '**/mise.toml') }}",
            content,
        )
        self.assertIn("**/node_modules", content)
        self.assertIn("~/.local/share/pnpm/store", content)
        self.assertIn("inputs.js == 'true'", content)
        self.assertNotIn("upload-artifact", content)
        self.assertNotIn("download-artifact", content)
        self.assertNotIn("vendor-bundle.tar", content)

    def test_js_deps_uses_actions_cache_only(self):
        content = (ACTIONS_DIR / "js-deps" / "action.yml").read_text()
        self.assertIn("uses: actions/cache@", content)
        self.assertIn("**/node_modules", content)
        self.assertIn("~/.local/share/pnpm/store", content)
        self.assertNotIn("upload-artifact", content)
        self.assertNotIn("download-artifact", content)
        self.assertNotIn("node-modules.tar", content)

    def test_check_jobs_need_install_and_do_not_reinstall(self):
        for workflow_name in ("ci-ruby.yml", "ci-js.yml"):
            content = (WORKFLOWS_DIR / workflow_name).read_text()
            self.assertIn("needs: install", content, workflow_name)
            self.assertEqual(
                content.count("mode: install"),
                1,
                f"{workflow_name} should install deps only in the install job",
            )

    def test_ci_rails_is_thin_wrapper_over_ci_ruby(self):
        rails = (WORKFLOWS_DIR / "ci-rails.yml").read_text()
        self.assertIn(
            "uses: forsbergplustwo/github-actions/.github/workflows/ci-ruby.yml@",
            rails,
        )
        self.assertIn("rails: true", rails)
        self.assertNotIn("setup-rails", rails)
        self.assertNotIn("run: mise run", rails)
        self.assertNotIn("services:", rails)

    def test_commit_autofixes_only_stages_tracked_files(self):
        action = (ACTIONS_DIR / "commit-autofixes" / "action.yml").read_text()
        self.assertIn("git add -u", action)
        self.assertNotIn("git add -A", action)

    def test_ruby_implementation_does_not_call_split_setup_actions(self):
        content = (WORKFLOWS_DIR / "ci-ruby.yml").read_text()
        self.assertNotIn("setup-mise", content)
        self.assertNotIn("ruby-deps", content)
        self.assertNotIn("js-deps", content)

    def test_ci_ruby_rails_mode_restores_js_on_test(self):
        content = (WORKFLOWS_DIR / "ci-ruby.yml").read_text()
        test_job = content.split("\n  test:\n", 1)[1].split("\n  rubocop:\n", 1)[0]
        self.assertIn("js: ${{ inputs.rails }}", test_job)
        self.assertIn("image: ${{ inputs.rails && inputs.postgres_image || '' }}", test_job)
        self.assertIn("image: ${{ inputs.rails && 'redis:alpine' || '' }}", test_job)

    def test_dep_actions_are_not_used_for_workflow_artifacts(self):
        for workflow_name in ("ci-ruby.yml", "ci-js.yml"):
            content = (WORKFLOWS_DIR / workflow_name).read_text()
            self.assertNotIn("download-artifact", content, workflow_name)
            self.assertNotIn("vendor-bundle", content, workflow_name)
            self.assertNotIn("node-modules.tar", content, workflow_name)

    def test_jobs_are_separate_checks(self):
        ruby = (WORKFLOWS_DIR / "ci-ruby.yml").read_text()
        self.assertIn("\n  test:\n", ruby)
        self.assertIn("\n  rubocop:\n", ruby)
        self.assertIn("\n  brakeman:\n", ruby)
        self.assertNotIn("run: mise run ci", ruby)

    def test_autofix_uses_shared_commit_action(self):
        action = (ACTIONS_DIR / "commit-autofixes" / "action.yml").read_text()
        self.assertIn('git commit -m "Apply ${{ inputs.name }} autofixes"', action)
        self.assertIn("inputs.step_outcome == 'failure'", action)
        for workflow_name, tool in (("ci-ruby.yml", "RuboCop"), ("ci-js.yml", "Prettier")):
            content = (WORKFLOWS_DIR / workflow_name).read_text()
            self.assertIn("uses: $/.github/actions/commit-autofixes", content, workflow_name)
            self.assertIn(f"name: {tool}", content, workflow_name)
            self.assertNotIn("git config user.name", content, workflow_name)
            self.assertNotIn("autofixes_found=", content, workflow_name)

    def test_bundle_env_is_workflow_level_for_ruby(self):
        content = (WORKFLOWS_DIR / "ci-ruby.yml").read_text()
        self.assertEqual(
            content.count("BUNDLE_PATH: ${{ github.workspace }}/vendor/bundle"),
            1,
        )
        self.assertEqual(content.count("BUNDLE_GITHUB__COM:"), 1)


class ReadmeContractTests(unittest.TestCase):
    def test_readme_documents_workflows(self):
        content = (ROOT / "README.md").read_text()
        for workflow in ("ci-rails.yml", "ci-ruby.yml", "ci-js.yml", "deploy.yml"):
            self.assertIn(workflow, content)

    def test_readme_documents_tasks(self):
        content = (ROOT / "README.md").read_text()
        for task in ("test", "lint:ruby", "security", "lint:erb", "lint:js"):
            self.assertIn(f"`{task}`", content)

    def test_readme_includes_caller_examples(self):
        content = (ROOT / "README.md").read_text()
        self.assertIn("ci-rails.yml@main", content)
        self.assertIn("ci-ruby.yml@main", content)
        self.assertIn("ci-js.yml@main", content)
        self.assertIn("test: true", content)
        self.assertIn("branches: [main]", content)

    def test_readme_documents_shared_install_via_cache(self):
        content = (ROOT / "README.md").read_text()
        self.assertIn("Install", content)
        self.assertIn("actions/cache", content)
        self.assertIn("needs: install", content)
        self.assertIn("setup-rails", content)

    def test_readme_documents_ci_rails_as_wrapper(self):
        content = (ROOT / "README.md").read_text()
        self.assertIn("thin wrapper", content)
        self.assertIn("`rails: true`", content)


if __name__ == "__main__":
    unittest.main()
