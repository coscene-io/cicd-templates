# reusable-workflow

`image-push-go.yml` accepts an optional `skaffold-file` string, relative to
`workspace` (default `.`). It defaults to `skaffold.yaml`, preserving existing
callers. Both the image build and release tag lookup use the selected config.

```yaml
jobs:
  image-push:
    uses: coscene-io/cicd-templates/.github/workflows/image-push-go.yml@main
    with:
      project: video-split-analysis
      skaffold-file: skaffold.analysis.yaml
    secrets: inherit
```

`copy-timeout-minutes` optionally increases the Volcengine copy job budget for
large images (default `15`). For example, GPU image callers can set it to `45`.
It is forwarded to `cp-image-to-volcengine.yml` as `timeout-minutes`; direct
callers of that workflow retain the same 15-minute default.

`image-push-pnpm.yml` accepts an optional `package` script name (default empty).
When set, it runs after `build` and before image packaging, in a separate step
with `PNPM_CONFIG__AUTH` for private dependency metadata. The ordinary build step
does not receive that credential. Node/pnpm setup and the frozen install still
run only once. Existing callers that omit `package` retain their current flow.

For example, Gidle builds JavaScript with `build: gidle:build`, then assembles
its production dependency closure with `package: gidle:package:release`.
`pnpm deploy` reuses the installed store but may need online registry metadata
for its pruned lockfile's supply-chain checks; it is not guaranteed to work
with `--offline`. Resource measurement records `pnpm-package.time` separately.

The pnpm setup step sets `NODE_USE_ENV_PROXY=1` so its Node.js `fetch`
downloader honors the runner's `HTTP_PROXY`, `HTTPS_PROXY`, and `NO_PROXY`
settings when fetching the pnpm executable.
