# Reusable workflows

## pnpm image builds

`image-push-pnpm.yml` runs a host build only when the `build` input is nonempty.
For these builds, `pnpm/setup@v3` provisions Node.js and pnpm and performs one
frozen install before running the requested package script:

- `pnpm_version` overrides the package manager version; when empty, the action
  reads the caller's `package.json`.
- A root `.node-version` selects Node.js. Without it, the workflow retains its
  Node 24 fallback; it does not switch to the action's moving LTS default.
- A root `pnpm-lock.yaml` is required and must describe the install.
- `package_manager_cache` defaults to `false`.
  [Mono measurements](https://github.com/coscene-io/mono/pull/3385) on the current
  `cos-m` runners found that restoring and saving the pnpm store costs more than
  downloading dependencies for that workload.
  Callers on other runners can explicitly enable it after measuring total setup
  and post-action time.
- The small lockfile verification cache remains enabled independently of the
  store cache. Its key includes `pnpm-lock.yaml` and `pnpm-workspace.yaml`, when
  present, so dependency or workspace policy changes get a new cache entry.
- The caller's pnpm verification and package-manager policies are preserved;
  the template does not override `trustLockfile` or `pmOnFail`.

Package-registry credentials are passed to the setup/install step. When `build`
is empty, the workflow skips host Node/pnpm setup and dependency installation;
Skaffold and the caller's Dockerfile continue to own the image build. This does
not configure Docker/BuildKit caches or propagate host environment settings
into a Docker build.
