# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository purpose

This repository maintains Feather source metadata:
- `app/*.json` contains per-app source definitions.
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

### Tests / lint

No test suite or lint configuration is present in this repository. Validate changes by running the relevant script(s) directly and inspecting the changed JSON output.

There is also no single-test command available because no automated test runner is configured.

## High-level architecture

### Update pipeline

The release update flow starts in `scripts/update_repos.py`:
- loads configuration via `ConfigManager.create()`
- initializes logging
- constructs `RepositoryUpdater`
- fetches the latest GitHub release for each configured repo
- updates the target app JSON file in place

`RepositoryUpdater` in `feather/services/updater.py` is the core of this flow:
- reads tracked repositories from `config/repos.yml`
- uses `GitHubClient` to fetch the latest release
- selects the first release asset whose filename ends with `.ipa`
- loads the destination JSON file
- updates only `apps[0]` in that file
- refreshes version metadata and prepends a new `versions` entry when needed

### Merge pipeline

The catalog merge flow starts in `scripts/merge_apps.py`:
- forces the working directory to the repo root
- loads config and logger
- constructs `AppMerger`
- scans `app/*.json`
- merges all app entries into `all.json`

`AppMerger` in `feather/services/merger.py`:
- loads existing `all.json`
- preserves top-level metadata outside the `apps` array
- converts app payloads into `AppInfo`
- keys entries by `name` first, then `bundleIdentifier`
- replaces an app entry when any field differs
- sorts the final `apps` list by `name`

### Data model

`feather/models/app.py` defines the schema used by both flows:
- `AppInfo` represents an app entry
- `VersionEntry` represents historical versions
- unknown fields are preserved through `extra_fields`

That preservation matters because the per-app JSON files contain Feather-specific metadata beyond the core Python model. Avoid rewriting app JSON through a narrowed schema unless that is the explicit goal.

## Important files

- `config/repos.yml`: tracked upstream GitHub repositories and output paths
- `scripts/update_repos.py`: update entrypoint
- `scripts/merge_apps.py`: merge entrypoint
- `feather/services/updater.py`: release-fetch and per-app JSON update logic
- `feather/services/merger.py`: merge logic for `all.json`
- `feather/services/github_client.py`: PyGithub wrapper, requires `GITHUB_TOKEN`
- `.github/workflows/update-all-repos.yml`: scheduled automation that runs both scripts and commits the resulting JSON changes

## Repository conventions and gotchas

- `ConfigManager.create()` prefers `config/repos.yml`, but falls back to hardcoded defaults on any exception. If config changes seem ignored, check whether YAML loading failed silently.
- `RepositoryUpdater` updates only the first app entry in each per-app file (`apps[0]`). If a source file contains multiple apps, only the first is release-driven.
- The updater currently ignores `ipa_filename_pattern` from `config/repos.yml` and simply picks the first `.ipa` asset.
- `versionDate` is derived from the GitHub release publish time, while `versions[].date` is generated from the local current date during the update run. These can differ.
- Merge identity is `name or bundleIdentifier`; duplicate names across apps would collide during merge.
- `scripts/merge_apps.py` normalizes the working directory to the repo root; `scripts/update_repos.py` only adjusts `sys.path`, so running from the repo root is the safest default.

## CI automation

GitHub Actions in `.github/workflows/update-all-repos.yml`:
- runs daily and on manual dispatch
- uses Python 3.11
- installs `requirements.txt`
- runs `python scripts/update_repos.py` and `python scripts/merge_apps.py`
- commits and pushes changed JSON files back to `main`
