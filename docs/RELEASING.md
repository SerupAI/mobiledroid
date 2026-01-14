# Release Process

Guidelines for versioning, tagging, and releasing MobileDroid.

---

## Semantic Versioning (SemVer)

We follow [Semantic Versioning](https://semver.org/): `MAJOR.MINOR.PATCH`

| Bump | When to Use | Examples |
|------|-------------|----------|
| **PATCH** (0.0.x) | Bug fixes, small tweaks, docs | "Fixed null check", "Updated README" |
| **MINOR** (0.x.0) | New features, backward compatible | "Added proxy system", "New API endpoint" |
| **MAJOR** (x.0.0) | Breaking changes | "Changed API format", "Removed endpoint" |

### Pre-1.0 Rules
While version is `0.x.x`:
- API is considered unstable
- Minor bumps may include breaking changes
- Move to `1.0.0` when ready for production stability commitment

### Examples
```
v0.0.13 → v0.0.14  # Bug fix
v0.0.14 → v0.1.0   # New feature (fingerprinting, proxy system)
v0.1.0  → v0.2.0   # Another feature
v0.2.0  → v1.0.0   # Production ready, stability commitment
v1.0.0  → v1.0.1   # Bug fix
v1.0.1  → v1.1.0   # New feature (backward compatible)
v1.1.0  → v2.0.0   # Breaking API change
```

---

## Release Checklist

Before tagging a release:

- [ ] All tests pass (`pytest tests/ -v`)
- [ ] No uncommitted changes (`git status`)
- [ ] CHANGELOG.md updated (if exists)
- [ ] Version bumped in code (if applicable)
- [ ] Documentation updated for new features

---

## How to Release

### 1. Commit All Changes
```bash
git add -A
git commit -m "feat: description of changes"
```

### 2. Push to Main
```bash
git push origin main
```

### 3. Create Annotated Tag
```bash
# Simple tag
git tag -a v0.2.0 -m "Brief description"

# Tag with release notes
git tag -a v0.2.0 -m "$(cat <<'EOF'
## What's New
- Feature 1 description
- Feature 2 description

## Bug Fixes
- Fixed issue X
- Fixed issue Y

## Breaking Changes
- None (or list them)
EOF
)"
```

### 4. Push Tag
```bash
git push origin v0.2.0
```

### 5. Create GitHub Release (Optional)
- Go to GitHub → Releases → "Create release"
- Select the tag
- Add detailed release notes
- Attach any artifacts if needed

---

## Conventional Commits (Recommended)

Use conventional commit messages for clarity and future automation:

```
feat: add WebGL fingerprint spoofing
fix: resolve proxy connection timeout
docs: update API documentation
refactor: simplify fingerprint service
test: add unit tests for proxy pool
chore: update dependencies
```

### Format
```
<type>: <description>

[optional body]

[optional footer]
```

### Types
| Type | Description | Version Bump |
|------|-------------|--------------|
| `feat` | New feature | Minor |
| `fix` | Bug fix | Patch |
| `docs` | Documentation only | None (or Patch) |
| `refactor` | Code change, no behavior change | None |
| `test` | Adding tests | None |
| `chore` | Maintenance, dependencies | None |

### Breaking Changes
Add `!` after type or `BREAKING CHANGE:` in footer:
```
feat!: change API response format

BREAKING CHANGE: Response now returns array instead of object
```

---

## Release Notes

### What to Include
1. **What's New** - New features and capabilities
2. **Improvements** - Enhancements to existing features
3. **Bug Fixes** - Issues resolved
4. **Breaking Changes** - What users need to change
5. **Deprecations** - What will be removed in future
6. **Contributors** - Credit to contributors (for OSS)

### Example Release Notes
```markdown
## v0.2.0 - 2026-01-20

### What's New
- **WebGL Fingerprinting**: Added GL renderer and vendor spoofing
- **Proxy Health Checks**: Automatic proxy validation before use

### Improvements
- Fingerprint injection now sets 35+ parameters (up from 27)
- Task queue retry logic improved

### Bug Fixes
- Fixed proxy connection timeout on slow networks (#123)
- Fixed screenshot memory leak (#124)

### Breaking Changes
- None

### Contributors
- @username - Proxy health check implementation
```

---

## Automation (Future)

When ready to automate releases:

### Option 1: release-please (Google)
- Parses conventional commits
- Auto-creates release PRs
- Generates CHANGELOG.md

```yaml
# .github/workflows/release-please.yml
name: Release Please
on:
  push:
    branches: [main]
jobs:
  release-please:
    runs-on: ubuntu-latest
    steps:
      - uses: google-github-actions/release-please-action@v4
        with:
          release-type: python
```

### Option 2: semantic-release
- Fully automated versioning
- Publishes to package registries
- Creates GitHub releases

### Option 3: Manual with Templates
- Use GitHub Release template
- Keep CHANGELOG.md manually updated

---

## Version Locations

When bumping versions, update these files:

| File | Field |
|------|-------|
| `packages/api/src/config.py` | `app_version` |
| `packages/ui/package.json` | `version` |
| `docker/docker-compose.yml` | Image tags (if hardcoded) |

---

## Hotfix Process

For urgent production fixes:

```bash
# Create hotfix branch from tag
git checkout -b hotfix/v0.1.1 v0.1.0

# Make fix
git commit -m "fix: critical security issue"

# Tag and push
git tag -a v0.1.1 -m "Hotfix: critical security issue"
git push origin v0.1.1

# Merge back to main
git checkout main
git merge hotfix/v0.1.1
git push origin main
```

---

## SaaS Submodule Updates

When updating the core submodule in mobiledroid-saas:

```bash
cd mobiledroid-saas/core
git fetch --tags
git checkout v0.2.0
cd ..
git add core
git commit -m "chore: update core to v0.2.0"
git push
```

---

*Last updated: January 2026*
