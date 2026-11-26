<!--
Title: a conventional commit, e.g. "feat(api): add task snooze". It becomes the
squashed commit on main and drives the changelog and version bump.
-->

## What

<!-- What this changes, briefly. -->

## Why

<!-- The reason, or the design decision it implements. -->

## Testing

<!-- How it was tested: new or changed tests, and anything checked by hand on dev. -->

## Checklist

- [ ] Title is a conventional commit (`feat:`, `fix:`, `refactor:`, `test:`, `docs:`, `ci:`, `chore:`; `!` for breaking changes)
- [ ] `uv run pytest`, `uv run ruff check` and `uv run ruff format --check` pass
- [ ] Any database migration is forward-only
- [ ] New config has a default and is listed in `server/.env.example`
- [ ] Unfinished or risky behaviour is behind a feature flag
