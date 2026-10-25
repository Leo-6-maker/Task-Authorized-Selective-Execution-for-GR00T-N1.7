# GPU1 owner assignment and frozen entry restriction

**GPU1_RESOURCE_AUTHORIZED / NO_NATIVE_START / ZERO_NEW_TEST.** On2026-10-25 SGT the human owner explicitly instructed “你使用GPU1”. This supersedes the prior next-device preference, not the actual historical acquisition identity. All0001–0084 remain acquired on GPU0. The next requested device is GPU1; no automatic fallback to GPU0 is proposed.

Live inventory identifies GPU1 as RTX4080SUPER,total16376MiB,free10121MiB,one preexisting compute process,untouched. The exact authorized908 server launcher `scripts/e2_test_server.py:235` unconditionally requires free memory>=16384MiB. The device total itself is8MiB below that predicate. Therefore waiting for its current task to leave would address competition but would not make this exact launcher admissible. Current free memory is additionally6263MiB below the predicate. These are separate blockers.

CPU-only isolation executes the exact frozen AST predicate with the live GPU1 inventory and the original `require` helper. Actual child and recording-wrapper exits are1 with the expected insufficient-memory error. It does not call `serve`,model/allocator/simulator,or native server startup. Initial inventory inspection itself exited0; the earlier private `precheck_exit` indicator was a calculated failed condition, not a native process exit. The separately recorded subprocess receipt is the actual CPU guard exit. No executable/config/grant was edited.

The new allocation receipt binds GPU1 UUID and direct owner instruction privately. It records requested allocation only,not active server/admission. The original GPU0 allocation and all84 original reservations/results remain unchanged. Current ledger is84 consumed(61SUCCESS,10TIME_LIMIT,10SEMANTIC_ABORT,3 historical CLEANUP_ERROR0010/14/16),36NOT_STARTED,0085 absent. No model,MuJoCo or TEST request and no extra ID occurred in this resource check.

## Concrete next control point

An independent engineering reviewer must assess the hardware-specific resource entry restriction before this exact project can use GPU1. The affected line is the absolute16384MiB launcher predicate. This executor has not lowered it, supplied false memory,patched `require`,changed signed grants,or used another entry point. An acceptable future proposal must keep all scientific/admission/ledger invariants,account for actual pinned-server and native Shadow memory plus headroom,fail before reservation when insufficient,and provide CPU boundary/negative tests. Any resulting launcher or frozen-hash change requires a complete newly reviewed execution Head and a fresh exact-head TEST grant. No unreviewed cold-start/model diagnostic is requested or executed here.

Separately,GPU1 must have sufficient real available memory under the owner's allocation before startup. Another project's current process may not be killed by this agent. No automatic inference from owner device selection to sufficient capacity is made. Releasing memory alone cannot resolve the current absolute guard.

This is a resource/entry review request,not a scientific protocol amendment or a self-issued authorization. k3,TaskSpec,oracle,models,120 IDs,split/seeds,16/8/720 and all historical failures remain fixed. Actual source stays908bef373eedf8d008ad8d9a91478e3f719eecfb. No source fix has been implemented or granted by this report.
