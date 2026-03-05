# github-actions

This repo contains our re-usable Github Actions, used by our AppKit powered apps. AppKit automatically sets up the needed files to make everything work, but you do need to add the Action Secrets as shown below.

## Setup Action Secrets (required):
- BUNDLE_TOKEN - Github's Personal access token (info on how to create it below)
- MASTER_KEY - Rails credentials key from 1Password
- SHOPIFY_CLI_PARTNERS_TOKEN - https://shopify.dev/docs/apps/tools/cli/ci-cd#generate-a-cli-authentication-token-in-the-partner-dashboard

Add these to the repos secrets action settings. Example: https://github.com/forsbergplustwo/app_kit/settings/secrets/actions

#### To create a Personal access token:
1. Go to https://github.com/settings/tokens
1. Create new token with "repo" scope
1. Choose "No expiration" or set it to a high value (eg year) in repo settings:

## CI task contract (mise)

These reusable workflows are task-driven and execute `mise run <task>` in the caller repo.
Define these tasks in your app's `mise.toml`.

Required tasks:
- `setup`
- `ci`
- `test`
- `lint`
- `build`
- `dev`

Optional tasks:
- `deploy`
- `security`
- `format`
- `format:write`
- Framework-specific subtasks such as `lint:ruby` and `lint:erb`

### Rails `mise.toml` example

```toml
[tasks.setup]
run = [
  "sudo apt-get update && sudo apt-get install -y --no-install-recommends libvips",
  "bundle install --jobs 4 --retry 3",
  "cp .env.example .env",
  "RAILS_ENV=test bin/rails db:create db:schema:load db:migrate",
  "RAILS_ENV=test bin/rails assets:precompile",
]

[tasks.test]
run = "bin/rails test:all"

[tasks.lint]
run = [
  "# TODO: choose rubocop/standardrb command",
  "bundle exec standardrb",
]

[tasks.lint:ruby]
run = "bundle exec standardrb"

[tasks.lint:erb]
run = "bundle exec erb_lint app/views --format compact"

[tasks.security]
run = "bundle exec brakeman -q"

[tasks.ci]
depends = ["setup", "test"]

[tasks.build]
run = "bin/rails assets:precompile"

[tasks.dev]
run = "bin/dev"

[tasks.deploy]
run = "# TODO: choose your deploy command"
```

### Nuxt `mise.toml` example

```toml
[tasks.setup]
run = [
  "corepack enable",
  "pnpm install --frozen-lockfile",
]

[tasks.test]
run = "pnpm test"

[tasks.lint]
run = "pnpm lint"

[tasks.format]
run = "pnpm prettier --check ."

[tasks.format:write]
run = "pnpm prettier --write ."

[tasks.ci]
depends = ["setup", "lint", "test"]

[tasks.build]
run = "pnpm build"

[tasks.dev]
run = "pnpm dev"

[tasks.deploy]
run = "# TODO: choose your Nuxt deployment command"
```

### Next.js `mise.toml` example

```toml
[tasks.setup]
run = [
  "corepack enable",
  "pnpm install --frozen-lockfile",
]

[tasks.test]
run = "pnpm test"

[tasks.lint]
run = "pnpm lint"

[tasks.format]
run = "pnpm prettier --check ."

[tasks.format:write]
run = "pnpm prettier --write ."

[tasks.ci]
depends = ["setup", "lint", "test"]

[tasks.build]
run = "pnpm build"

[tasks.dev]
run = "pnpm dev"

[tasks.deploy]
run = "# TODO: choose your Next.js deployment command"
```

## Manual setup (non AppKit powered repo)
- Add master.key and bundle token to repos secrets, as mentioned above
- Add `.github/workflows` folder in repo root
- Add a file named `ci.yml`:

```yaml
name: Tests

on: [push]

jobs:
  build:
    uses: forsbergplustwo/github-actions/.github/workflows/ci.yml@main
    with:
      app_name: ddp
    secrets:
      master_key: ${{ secrets.MASTER_KEY }}
      bundle_token: ${{ secrets.BUNDLE_TOKEN }}

```

- Add a file named: `prettier.yml`:

```yaml
name: Prettier

on:
  pull_request:
    branches: [main]

jobs:
  prettier:
    uses: forsbergplustwo/github-actions/.github/workflows/prettier.yml@main
    secrets:
      bundle_token: ${{ secrets.BUNDLE_TOKEN }}
```

- Add a file named `reviewdog.yml`:

```yaml
name: Reviewdog

on: [pull_request]

jobs:
  standard:
    uses: forsbergplustwo/github-actions/.github/workflows/standard.yml@main
    secrets:
      bundle_token: ${{ secrets.BUNDLE_TOKEN }}

  brakeman:
    uses: forsbergplustwo/github-actions/.github/workflows/brakeman.yml@main
    secrets:
      bundle_token: ${{ secrets.BUNDLE_TOKEN }}
```

All reusable workflows above call `mise run <task>` in your repository. Ensure your `mise.toml` implements the required task contract.
