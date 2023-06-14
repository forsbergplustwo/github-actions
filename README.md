# github-actions

This repo contains our re-usable Github Actions, used by our AppKit powered apps. AppKit automatically sets up the needed files to make everything work, but you do need to add the Action Secrets as shown below.

## Setup Action Secrets (required):
- BUNDLE_TOKEN - Github's Personal access token (info on how to create it below)
- MASTER_KEY - Rails credentials key from 1Password

Add these to the repos secrets action settings. Example: https://github.com/forsbergplustwo/app_kit/settings/secrets/actions

#### To create a Personal access token:
1. Go to https://github.com/settings/tokens
1. Create new token with "repo" scope
1. Choose "No expiration" or set it to a high value (eg year) in repo settings: 


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
