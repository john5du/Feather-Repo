# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository purpose

This repository maintains Feather source metadata:
- `app/*.json` contains per-app source definitions (source of truth).
- `all.json` is the merged catalog consumed as the repository-wide source.
- The Python code updates app metadata from upstream GitHub releases, then merges all app definitions into `all.json`.

## Common commands

Run commands from the repository root.

### Setup

```bash
pip install -r requirements.txt
```

### Update app JSON files from GitHub releases

Requires `GITHUB_TOKEN` in the environment.

```bash
python scripts/update_repos.py
```

### Merge `app/*.json` into `all.json`

```bash
python scripts/merge_apps.py
```

### Full local refresh

```bash
python scripts/update_repos.py && python scripts/merge_apps.py
```

### Tests

```bash
python -m unittest discover -s tests -v
```

No separate lint configuration is present. Validate changes with the unit tests and by running the relevant script(s).

## High-level architecture

### Update pipeline

The release update flow starts in `scripts/update_repos.py`:
- loads configuration via `ConfigManager.create()`
- initializes logging
- constructs `RepositoryUpdater`
- fetches the latest GitHub release for each configured repo (concurrent workers)
- updates the matching app entry in the target JSON file

`RepositoryUpdater` in `feather/services/updater.py`:
- reads tracked repositories from `config/repos.yml`
- uses `GitHubClient` (retry + rate-limit aware) to fetch the latest release
- selects IPA assets by ordered `ipa_filename_pattern` list (`fnmatch`)
- selects the target app deterministically (single app, exact name, or bundle match)
- validates app payload before writeback
- treats any per-repo error as overall failure (`result.success=False`)

### Merge pipeline

The catalog merge flow starts in `scripts/merge_apps.py`:
- forces the working directory to the repo root
- loads config and logger
- constructs `AppMerger`
- scans `app/*.json`
- merges all app entries into `all.json`
- removes orphan apps not present in source files when `merge.remove_orphans` is true

### Data model

`feather/models/app.py` defines the schema used by both flows:
- `AppInfo` uses Feather field names (`developerName`, `iconURL`, `localizedDescription`, ...)
- `VersionEntry` represents historical versions
- unknown fields and original key order are preserved
- optional known fields are not injected solely because of defaults

## Important files

- `config/repos.yml`: tracked upstream GitHub repositories and output paths
- `scripts/update_repos.py`: update entrypoint
- `scripts/merge_apps.py`: merge entrypoint
- `feather/services/updater.py`: release-fetch and per-app JSON update logic
- `feather/services/merger.py`: merge logic for `all.json`
- `feather/services/github_client.py`: PyGithub wrapper, requires `GITHUB_TOKEN`
- `.github/workflows/update-all-repos.yml`: scheduled automation that tests, updates, merges, and commits JSON changes

## Repository conventions and gotchas

- `ConfigManager.create()` loads `config/repos.yml` and raises on failure (no silent fallback).
- IPA matching uses ordered patterns; first matching pattern wins, then first matching asset.
- Version tags are normalized by stripping leading `v/V`, known suffixes, and `+build`.
- Merge identity is `bundleIdentifier or name`.
- Both entrypoint scripts `chdir` to the repository root before running.
- JSON saves use stable indentation and a trailing newline.

## CI automation

GitHub Actions in `.github/workflows/update-all-repos.yml`:
- runs daily and on manual dispatch
- uses Python 3.11
- installs pinned-range dependencies from `requirements.txt`
- runs unit tests
- runs `python scripts/update_repos.py` then `python scripts/merge_apps.py`
- commits and pushes only when previous steps succeed
