# Contributing

## Environments and release channels

Each environment is named after the release channel it runs. The channel is built into the image (`RELEASE_CHANNEL`) and shown by `/version`.

| Channel | Source | Updates | Data |
| --- | --- | --- | --- |
| `dev` | A local working copy, run with auto-reload | On every save | Its own disposable database |
| `edge` | The `:edge` image, built from every merge to `main` | Automatically | Its own database |
| `stable` | The `:stable` image, built from release tags | Manually | The real data |

- Every channel except `stable` shows a floating badge in the web UI. It also holds developer menus. Stable never shows it.
- Each environment has its own database. Data only ever flows down (stable → edge, e.g. to test migrations against real data), never back up.

## Image tags

Images are published to `ghcr.io/owentourlamain/todo-server`:

- `:edge` and `:sha-<commit>` for every merge to `main`
- `:X.Y.Z`, `:X.Y` and `:stable` for each release

## Branches, commits and pull requests

- Branch from the latest `main` and name it `<type>/<short-kebab-description>`, e.g. `feat/task-schema`.
- Types: `feat`, `fix`, `refactor`, `test`, `docs`, `ci`, `chore`.
- Pull request titles are [conventional commits](https://www.conventionalcommits.org/). An optional scope says which part changed: `feat(api): …`, `fix(scheduler): …`, `feat(web): …`.
- Pull requests are squash-merged, so the title becomes the commit on `main`, and the changelog and version bump are generated from it.
- Keep each pull request to one logical change.
- Breaking changes use `!` (`feat!: …`) and a `BREAKING CHANGE:` note in the description.
- `main` is protected: changes need a pull request and passing CI (lint, tests, Docker build).

## Versioning

SemVer, `0.MINOR.PATCH` until the first stable release: features bump the minor version, fixes bump the patch version. Breaking changes also bump the minor version while in `0.x`.

## Development loop

1. Branch from `main`, then build the change with tests.
2. Try it on a `dev` instance.
3. Push the branch and open a pull request; CI must pass.
4. Squash-merge. `edge` picks up the new image automatically.
5. Use it on `edge`. When it's ready, merge the release pull request to publish `stable`.
6. Fixes go to `main` first, then out in a patch release.

## Local setup

The server is a [uv](https://docs.astral.sh/uv/) project in `server/`:

```sh
cd server
uv sync
RELEASE_CHANNEL=dev uv run uvicorn --factory todo_server.app:create_app --reload --reload-dir src
uv run pytest
uv run ruff check && uv run ruff format --check
```

Configuration is by environment variables; see `server/.env.example`.

## Database migrations

Migrations are forward-only. Never edit a migration that has been merged; add a new one.

## Feature flags

Flags are defined in code with a stage:

- `experimental`: only on `dev` and `edge`.
- `beta`: users can opt in on `stable`.
- `stable`: always on; the flag is then removed.
