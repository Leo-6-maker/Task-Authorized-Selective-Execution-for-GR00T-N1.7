# Compact submission source snapshot — archive only

This branch is a curated source distribution, not an implementation change and **must not be merged into the development branch**. Use the separately created final-integration PR for documentation changes.

The native modules, configs, tests, external operator and original review checker reuse existing Git trees byte-for-byte. The archive contains compact immutable E2 results, full final E3 public results, source-lock R015 evidence and selected reconciliation/authorization-preparation records. It omits unrelated bulk history, private raw trajectories/weights/machine secrets. Full experiment history remains at the immutable source commits in SOURCE_PROVENANCE.json.

Run `python tools/verify_release.py --repo .` for a standard-library exported-data recount; add `--full-e3` after installing NumPy for the original public bootstrap checks. Full native/history-sensitive unit tests require the original repository and environment; the ZIP does not contain a `.git` directory.

Delivered PPTX/PDF are separate course artifacts. The exact builder and file hashes are under submission/. Submit the chosen slide file plus this source ZIP. No new experiments are permitted.
