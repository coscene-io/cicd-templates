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
