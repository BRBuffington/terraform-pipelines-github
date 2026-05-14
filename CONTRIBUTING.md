# Contributing

## Git workflow

Lifted from `~/.claude/rules/sdlc-engineer.instructions.md`. Applies to every change.

### Feature branch only — never commit to `main`

1. `git checkout main && git pull --rebase`
2. `git checkout -b feat/<desc>` (or `fix/<desc>`)
3. Work, run tests
4. `git pull --rebase origin main` before pushing
5. `git push -u origin <branch>`
6. Open PR, fast-forward merge after review
7. Delete branch local + remote immediately after merge

### Commit hygiene

- **Atomic commits.** One logical change per commit, minimum file count.
- **Push after every change.** Don't accumulate local commits.
- **Never force-push** to a shared branch. Rebase + resolve manually.
- **Never use `-X ours`** on cross-remote merges — it silently drops files.
- Use Conventional Commit prefixes: `feat:`, `fix:`, `chore:`, `docs:`, `refactor:`, `test:`.

### After every push

Show the user links to all configured remotes so they can verify.

## Workflow changes

Both reusable workflows in `.github/workflows/` are consumed by other repos pinned to a tag or `@main`. Breaking changes:

1. Make the change on a feature branch.
2. Open a PR; CI is best-effort (no self-test in this repo yet).
3. After merge, **tag a new version** (`git tag v1.x.y && git push --tags`).
4. Notify consumers to pin to the new tag.

Until v1.0.0, consumers may track `@main`.

## Backend (azurerm) reference

The reusable `terraform-cd.yml` injects backend config via `-backend-config=` flags. Consumers must declare an empty backend block in their `providers.tf`:

```hcl
terraform {
  backend "azurerm" {}
}
```

Recommended backend storage account properties (informed by hard lessons):

- **Disable shared key auth** on the storage account. Use AAD auth: workflow passes `use_azuread_auth=true`.
- **Use OIDC** end-to-end: `use_oidc=true` flag is set by the workflow when `ARM_USE_OIDC=true`.
- **Resource group naming**: keep it short and consistent. `tfstate-rg` works (not `rg-tfstate`).
- **Key path**: `<TF_BACKEND_KEY_PREFIX>/<config>.tfstate` (one state file per environment matrix entry).
- **Lock**: azurerm backend uses blob lease for locking automatically.

App registration permissions:
- `Storage Blob Data Contributor` on the storage account (NOT `Contributor` on the RG — too broad).
- `Contributor` on the **target** subscription where resources are deployed.
