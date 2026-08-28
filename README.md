# StereoPatch project page

Static Astro project page for **StereoPatch: Patch-Aligned RGB--Depth Fusion for Spatial Perception in Robot Manipulation**.

## Local development

```sh
pnpm install
pnpm dev
```

## Evidence boundary

- Quantitative values are transcribed from the current paper tables and retain their original denominators.
- `public/paper/stereopatch-preprint.pdf` is synchronized with the current compiled manuscript before release.
- Task videos are selected qualitative rollouts and are not rollout denominators.
- `N_eff` is a render-level diagnostic, not a cross-resolution activation metric.
- RQ5 serial rows are componentwise latency budgets, not synchronized end-to-end quantiles.
- Evidence motion is progressive enhancement: exact values remain visible without JavaScript and all animation is disabled under reduced-motion preferences.

## Media delivery

- The original edited 4K60 rollouts remain archived in the `media-v1` GitHub Release.
- The page selects complete 1080p60 streams on desktop and complete 720p30 streams on compact or constrained connections; timing and playback semantics are unchanged.
- Evidence videos receive a source only when selected for playback. Inactive and offscreen players are paused and released to keep one ordinary decoder active.

## Intended deployment

- Source: an independent GitHub repository named `stereopatch`.
- Public URL: `https://yananzhou.me/stereopatch/`.
- Hosting: GitHub Pages project site. The existing `YananZHOU5555.github.io` repository continues to own the `yananzhou.me` custom domain; this project does not add its own `CNAME`.
- Build: pushing `main` triggers `.github/workflows/deploy.yml` and publishes `dist/`.

The project is deliberately separate from the current personal-site worktree, so the page can evolve without overwriting unrelated local changes.
