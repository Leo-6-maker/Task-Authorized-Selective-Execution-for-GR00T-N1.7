# Issue31 CPU handoff

Start with `REVIEW_REQUEST.md`, `E3_AUTONOMOUS_STATUS.json`, `PLAN_BASELINE.md` and the complete charter. The code/protocol is proposed, native runtime unexecuted. E2 PR30 scientific R3 and course fallback remain priorities.

CPU reproduction using the existing NumPy Python environment (no model/simulator installation):

```bash
python -m unittest discover -s tests -v
python -O -m unittest discover -s tests -v
python -m e3.cli verify-manifest --repo . --output manifest-check.json
```

Outputs must use new absent filenames; keep failures and actual exit receipts. `e3.cli audit` is read-only, requires explicit workspace, preserves all160 planned rows and never invokes native code. Native E3 entry points (`e3.server_launcher`, `e3.server`, `e3.supervisor`, `e3.native_runner`) require a separately current exact-Head independent E3 grant; proposed metadata and old R013 grants fail closed. `e3.scene_probe` has an independent bounded diagnostic grant path and remains NOT EXECUTED. No model/GPU/MuJoCo/TEST may start during this CPU delivery.

`E2_OFFLINE_EXPLORATORY.json` contains raw-source-bound post-hoc analysis, not revised E2 results. Full source mapping distinguishes actual B0 future contacts from saved G predictions. `E2_AUDIT_EQUIVALENCE.json` records fresh Corelab ordinary/-O output equality with final120. Source/compiled scene and runtime validation have separate status.
