# github-actions

Reusable GitHub Actions workflows for AppKit Rails apps, other Ruby repos, and JS lint. Callers only need a short workflow file and a `mise.toml` that implements the tasks below.

## Setup Action Secrets (required)

- `BUNDLE_TOKEN` - GitHub personal access token with `repo` scope (private gems)
- `MASTER_KEY` - Rails credentials key from 1Password (Rails callers)
- `SHOPIFY_CLI_PARTNERS_TOKEN` - https://shopify.dev/docs/apps/tools/cli/ci-cd#generate-a-cli-authentication-token-in-the-partner-dashboard (deploy only)

Example: https://github.com/forsbergplustwo/app_kit/settings/secrets/actions

### To create a Personal access token

1. Go to https://github.com/settings/tokens
1. Create a new token with the `repo` scope
1. Choose "No expiration" or a long expiry

## Workflows

| Workflow | Use for | Jobs (shown separately in the Actions UI) |
| --- | --- | --- |
| `ci-rails.yml` | Rails apps / AppKit | Thin wrapper → `ci-ruby.yml` with `rails: true` (Postgres, Redis, apt, JS, master key) |
| `ci-ruby.yml` | Gems, Sinatra, Jekyll, other Ruby (and the Rails implementation) | Install, Tests, RuboCop, Brakeman, ERB Lint |
| `ci-js.yml` | JS lint (and optional JS tests) | Install, Prettier, Tests |
| `deploy.yml` | Shopify app deploy | Deploy |

Call Rails apps with `ci-rails.yml` only (not both). `ci-rails` is a thin wrapper that calls `ci-ruby` with `rails: true`; all shared jobs live in `ci-ruby.yml`.

Each check is its own job. Do not fold them into a single `mise run ci` job.

Dependencies are installed **once** in the Install job and written to `actions/cache`. Check jobs use `needs: install`, then restore the same cache keys (`vendor/bundle` for Ruby, `node_modules` + pnpm store for JS). That covers both within-run sharing and reuse across PRs/branches when the lockfile is unchanged. Shared setup lives in composite actions under `.github/actions/` (`setup-rails` for checkout/mise/gems/JS, `cache-apt` for Aptfile packages, `commit-autofixes` for lint/format push-backs, `setup-mise` + `js-deps` for JS-only workflows).

## CI task contract (mise)

Workflows call `mise run <task>` in the caller repo.

| Task | Used by |
| --- | --- |
| `test` | Tests job |
| `lint:ruby` | RuboCop job |
| `security` | Brakeman job |
| `lint:erb` | ERB Lint job (off by default) |
| `lint:js` | Prettier job |

Also define install helpers the tasks depend on (`install`, `install:ruby`, `install:js`, `setup`) as needed.

### Rails `mise.toml` example

```toml
[tasks.install]
depends = ["install:ruby"]

[tasks."install:ruby"]
run = "bundle check || bundle install"

[tasks.setup]
depends = ["install:ruby"]
run = [
  "test -f .env || cp .env.example .env",
  "RAILS_ENV=test bin/rails db:create db:schema:load db:migrate",
]

[tasks.test]
depends = ["setup"]
run = "bin/rails test"

[tasks."lint:ruby"]
depends = ["install:ruby"]
run = "bin/rubocop -f github"

[tasks.security]
depends = ["install:ruby"]
run = "bundle exec brakeman -q"

[tasks."lint:js"]
depends = ["install:js"]
run = "pnpm run lint:js"
```

### Ruby gem `mise.toml` example

```toml
[tasks.install]
depends = ["install:ruby"]

[tasks."install:ruby"]
run = "bundle check || bundle install"

[tasks.test]
depends = ["install:ruby"]
run = "bundle exec rake test"

[tasks."lint:ruby"]
depends = ["install:ruby"]
run = "bundle exec rubocop -f github"
```

### Nuxt / Next.js `mise.toml` example

```toml
[tasks."install:js"]
run = "pnpm install --frozen-lockfile"

[tasks.test]
depends = ["install:js"]
run = "pnpm test"

[tasks."lint:js"]
depends = ["install:js"]
run = "pnpm run lint:js"
```

## Caller setup

### Rails app (with JS lint)

```yaml
name: CI

on: [push, pull_request]

concurrency:
  group: ci-${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: ${{ github.event_name == 'pull_request' }}

jobs:
  rails:
    permissions:
      contents: write
    uses: forsbergplustwo/github-actions/.github/workflows/ci-rails.yml@main
    with:
      app_name: your_app
      test: ${{ github.event_name == 'push' }}
    secrets:
      master_key: ${{ secrets.MASTER_KEY }}
      bundle_token: ${{ secrets.BUNDLE_TOKEN }}

  js:
    permissions:
      contents: write
    uses: forsbergplustwo/github-actions/.github/workflows/ci-js.yml@main
    secrets:
      bundle_token: ${{ secrets.BUNDLE_TOKEN }}
```

`test: ${{ github.event_name == 'push' }}` keeps the test suite on pushes so pull requests are not held up by the suite.

### Ruby gem / non-Rails repo

```yaml
name: CI

on: [push, pull_request]

concurrency:
  group: ci-${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: ${{ github.event_name == 'pull_request' }}

jobs:
  ruby:
    permissions:
      contents: write
    uses: forsbergplustwo/github-actions/.github/workflows/ci-ruby.yml@main
    with:
      brakeman: false
    secrets:
      bundle_token: ${{ secrets.BUNDLE_TOKEN }}
```

### `ci-rails.yml` inputs

| Input | Default | Notes |
| --- | --- | --- |
| `app_name` | required | Used for the default database name |
| `database_name` | `<app_name>_test` | Override when the DB name differs |
| `postgres_image` | `postgres:13-alpine` | |
| `test` | `false` | Turn on for push with the expression above |
| `rubocop` | `true` | |
| `brakeman` | `true` | |
| `lint_erb` | `false` | |
| `autofix` | `true` | RuboCop may commit and push fixes on pull requests |

### `ci-ruby.yml` inputs

| Input | Default |
| --- | --- |
| `test` | `true` |
| `rubocop` | `true` |
| `brakeman` | `false` |
| `lint_erb` | `false` |
| `autofix` | `true` |

### `ci-js.yml` inputs

| Input | Default |
| --- | --- |
| `prettier` | `true` |
| `test` | `false` |
| `autofix` | `true` |

Set a flag to `false` when that repo has no matching mise task. The job still appears as skipped.

Do not enable `pull_request_target` on caller workflows. These reusable workflows check out and run repository code with secrets, and they refuse `pull_request_target` callers.

## Deploy

```yaml
jobs:
  deploy:
    uses: forsbergplustwo/github-actions/.github/workflows/deploy.yml@main
    secrets:
      bundle_token: ${{ secrets.BUNDLE_TOKEN }}
      shopify_cli_token: ${{ secrets.SHOPIFY_CLI_PARTNERS_TOKEN }}
```

The caller repo must define `mise` task `deploy:shopify`.
