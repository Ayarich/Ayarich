# How to install on github.com/Ayarich/Ayarich

1. Unzip this package. Upload **the contents** (not the enclosing folder) into the `main` branch of `Ayarich/Ayarich`. Commit `README.md`, `scripts/generate.py`, `.github/workflows/contributions.yml`, and both starter images under `assets/`.
2. Visit https://github.com/settings/tokens and create a **classic** personal access token with `read:user` (access to profile contribution information). Do **not** add `repo` scope; the generator doesn't need to access repository contents. The token must belong to Ayarich.
3. At https://github.com/Ayarich/Ayarich/settings/secrets/actions create repository secret `GH_PROFILE_TOKEN` with that token. Never paste this token into README or code.
4. At repository Settings → Actions → General, make sure GitHub Actions is enabled and **Workflow permissions** allows **Read and write permissions**. GitHub Actions uses its built-in `GITHUB_TOKEN` to commit generated images, separate from your personal token.
5. Go to https://github.com/Ayarich/Ayarich/actions, select **Update GitHub contribution charts**, and click **Run workflow** on `main`.
6. When it shows a green check, inspect `assets/contributions.svg`, `assets/summary.svg`, and your profile page. The daily schedule then maintains them.

If you don't see the workflow: ensure the YAML file is on `main` at `.github/workflows/contributions.yml` (not inside another directory).

If it fails at generation: check the `GH_PROFILE_TOKEN` secret name, token owner, and `read:user` permission. Check whether SSO authorization is required for organization contributions.

If it fails at push with HTTP 403: confirm workflow write permissions and repository branch protection. Workflows can be restricted by organization policies.

The starter SVGs are explanatory placeholders and are **not** live contribution data. The action replaces them on first successful run.

GitHub counts only qualifying contributions; not every push or commit will be credited. Private activity included by the API depends on the authenticated viewer's permissions.
