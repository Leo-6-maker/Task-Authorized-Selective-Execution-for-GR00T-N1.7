# Reproducibility contract

## CPU engineering checks

Use an existing isolated Python3.12.14 environment with NumPy1.26.4. Both ordinary and optimized suites exercise real CPU subprocess proxies and temporary synthetic Git reviewers. They do not execute GR00T,MuJoCo or a real TEST ID.

```bash
CUDA_VISIBLE_DEVICES=-1 OPENBLAS_NUM_THREADS=1 python -m unittest discover -s tests -v
CUDA_VISIBLE_DEVICES=-1 OPENBLAS_NUM_THREADS=1 python -O -m unittest discover -s tests -v
```

Optional test-only evidence destinations:`TASE_CPU_LIFECYCLE_RECEIPTS` and `TASE_CPU_STARTUP_EVIDENCE`;use a fresh private directory for each run. Preserve actual failed fixture/child exits; a deliberately abnormal child does not mean a successful suite fabricated exit0.

## Historical original audit

A source ZIP alone cannot authenticate old Git blobs. Clone the full repository history and retain the independently reviewed report objects and main grant/revocation history. Use an authorized private original workspace whose files match the complete stopped archive SHA256 `cfe5f8357d2b48b473e95015f46dad933b1a17afbe830f6d83e1a2a30e85a76f`.

```bash
CUDA_VISIBLE_DEVICES=-1 OPENBLAS_NUM_THREADS=1 python scripts/e2_audit_test.py \
  --workspace <PRIVATE_ORIGINAL_WORKSPACE> --repo <FULL_HISTORY_CHECKOUT> \
  --output <NEW_PRIVATE_AUDIT_JSON>
```

This is read-only. It authenticates each historical grant/code/config/source identity. Suspended epochs need the reviewed consumed-prefix hashes. It preserves all120 denominators,old14,two CLEANUP_ERRORs and the exact predeclared statistics. It never unpickles saved snapshots or starts a model/simulator. Both raw original copies and every member require independent byte/hash verification.

## Future real execution boundary

The old R008 grant is suspended;R009 is superseded. None of these files grants model/GPU/MuJoCo/TEST access. Independent GPT must sign a new `TEST_AUTHORIZED` for the final complete reviewed Head. Scientific configs,model/processor/native versions and seeds remain frozen.

After that grant only:live legal resource/ownership/process/storage/model/source/preexisting14 and backup checks,new unique native session,0015 then0016 once,mandatory full checkpoint0016,and remaining fixed IDs in order with four-cell structural/worker/two-copy checks. Preserve failures permanently;never repeat0010/0014 or reset a ledger. Any actual program/monitor/resource/evidence fault stops real execution and returns to CPU engineering. Changed executable code requires another independent exact-head grant.
