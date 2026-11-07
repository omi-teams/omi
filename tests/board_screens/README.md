# Board browser QA

CI installs Playwright 1.56.1 and its Chromium headless shell. For workers,
uncomment the Browser QA block in the state repository's `docker/Dockerfile`
and rebuild the worker image. Other projects keep the block commented out.

Run `OMI_BROWSER_REQUIRED=1 python3 tests/test_omi.py` to fail when Node,
Playwright, or Chromium is unavailable. Set `OMI_BOARD_SCREENS` to a directory
outside the checkout to retain the twelve full-page PNGs (projects, dashboard,
task at 360/390/768/1280 px). CI uploads that directory even on failure.
Screenshots are evidence for review, not pixel-diff baselines. Do not commit them.

The browser checks run axe on every page and width in light and dark mode,
reject serious/critical violations, exercise keyboard controls, and check that
dashboard/task header controls disappear in print media. API requests must be
GET and all requests must stay on the board origin. The auditor is injected by
Playwright; it is not a production script or a CDN dependency.

## Vendored auditor

Required directory: `vendor/axe-core-4.11.0/`. Copy the unmodified `axe.min.js`
and MPL-2.0 `LICENSE` from the official pinned package
<https://registry.npmjs.org/axe-core/-/axe-core-4.11.0.tgz>.
Record both files with `sha256sum axe.min.js LICENSE > SHA256SUMS` from that
directory. The Python suite verifies the file set, version, license, and hashes;
the browser test never fetches the auditor at runtime.

The Coordinator supplied these files from `npm pack axe-core@4.11.0` and
verified the package integrity against the registry. Keep the vendored files
unchanged; no npm download is needed to run the auditor.

## Worker image measurement before merge

On the Docker host, record `docker image inspect --format '{{.Size}}' IMAGE`
before enabling the block, rebuild, and record the same value for the new image.
Report both byte counts and their difference to the PO. The Coordinator's
TASK-128 host measurement was **1.59 GB → 2.53 GB (+0.94 GB)**. This detached
container has no Docker client/daemon to repeat that measurement. The commented
template block adds no browser layer to projects that leave it disabled.
