# Reproduction levels — final coursework edition

## 1. Read and recount public results after ZIP extraction

Use `python tools/verify_release.py --repo .`. This standard-library entry point authenticates the immutable E2 ledger Git-blob identity, E3 audit/CSV/cross-check SHA256, original IDs, censoring, status/group counts and CSV consistency. It works without a `.git` directory. `--output NEW.json` refuses overwrite. `--self-test` runs five synthetic helper cases only.

With NumPy installed from `requirements-offline.txt`, use `python tools/verify_release.py --repo . --full-e3 --output NEW-full.json`. This additionally hashes all14 E3 data bindings and calls the unchanged original `review_tools.recheck_e3_final.analyze()` on the exported ledger, cells,36 checkpoints and21,527-row original inventory. It recomputes the frozen2000 paired task-stratified bootstrap/seed641500 without model/GPU/physics calls. It validates the public export, not private original bytes or historical Git-grant authenticity.

## 2. Rebuild the presentation

`python -m pip install -r submission/requirements-docs.txt`

`python submission/build_final_deck.py --output ME6401_TASE_Final_E2E3.pptx`

Export the PPTX to PDF with PowerPoint or LibreOffice. The supplied final PPTX/PDF were generated from this exact source and rendered to inspect all17 pages. Embedded ZIP timestamps/PDF export metadata may change hashes on rebuilding; compare slide content and render before replacing a delivered artifact. Do not redistribute fonts. Fill identity only when the owner supplies it.

## 3. Inspect original tests and historical code

Original native reference environments were separately pinned Linux/Python3.12.14 server/simulator roles; `configs/runtime_lock_E2.json` and source-bound receipts specify the actual packages, official weights and assets. NumPy1.26.4 is the minimal offline/reference dependency, not a complete native environment recipe.

Full unit/integration suites include real subprocesses, sockets, `/proc`, historical Git objects and source-specific fixtures. They are not promised to run unchanged from a history-free archive or a restricted sandbox. Use the full repository and original exact versions for historical test review. This package retains all native source and tests; it does not relax their authorization/source-lock checks. A new release commit is not a historical runtime identity.

Original E3 checker `python -m review_tools.recheck_e3_final --repo . --output NEW.json` requires the preserved historical main grant commits. The archive-friendly helper deliberately uses its pure `analyze()` entry instead; that is a different verification scope and is labeled as such.

## 4. No further native experiments

All120 E2 and160 E3 planned IDs are consumed. Model weights, LIBERO assets, raw videos/arrays, private machine paths, credentials and live resource records are not supplied. Do not repeat IDs, reuse historical permits or disable source locks. Any independent later research needs a separately defined study and permissions outside this course freeze.

## Actual packaging checks and limits

Confirmed exact Git-tree reuse of native/scientific code; exact-byte preservation of existing public result objects; generated17-page editable deck and PDF render/layout checks; five new helper synthetic tests passed ordinary/-O with actual exits0. No fresh full original-data run through the new helper, no282-case native-suite rerun, no private raw-file rehash and no GPU/model/simulator/TEST call occurred in packaging. These limits are explicit rather than fabricated PASS receipts.
