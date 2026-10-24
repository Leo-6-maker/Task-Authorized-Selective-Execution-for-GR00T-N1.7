# Lifecycle engineering delta

Scope:post-episode resource cleanup and necessary startup-failure cleanup. Prediction transport,Shadow.predict/receive,worker prediction block,E2Context.check/frame/capture/constructor,Gate/TaskSpec/oracle/controller and native admission/model startup remain semantically unchanged; see static proof.

The parent sends a unique close token. The owned worker acknowledges CLOSING,returns from native.close(),then emits CLOSED with PID/token/monotonic finalizer phases and closes its endpoint. Native errors emit CLOSE_ERROR and still produce a nonzero child exit. The parent reads bounded framed JSON in nonblocking mode only after prediction is finished,so a partial packet or backpressured request cannot hang cleanup. The original prediction payload/API remains unchanged.

Default cooperative finalizer budget10s,then at most2s for actual interpreter exit. Failed/unknown completion keeps an error even if final exit is0. Owned TERM and KILL fallback waits are each2s;every path closes the parent Pipe and releases a completed process handle. Nonzero exit,missing/invalid completion,deadline,forced request,unknown parent cleanup and surviving worker stay failures. Duplicate close returns the cached receipt or rethrows the cached failure. Startup errors retain their original exception and append the actual close receipt to traceback notes.

A clean G full outcome requires BOTH a valid native-finalizer handshake and actual worker exit0,matching PID/token,finite phase order,no force flags and closed parent resources. Old pre-protocol14 authenticate their original bytes and retain their original eligibility,never a fabricated new close receipt.

Corelab CPU regression additionally exposed a necessary existing server-wrapper race:forward INT,immediate finally TERM,actual native exit-15 instead of-2. The fix gives the already-forwarded signal a bounded shutdown window before existing TERM/KILL fallback. A deliberately delayed CPU INT handler makes the regression deterministic. Native exclusive directory creation,atomic admission,loaded/listener behavior and serve() remain unchanged. The old CPU failure is retained;this was not a real model/TEST incident.

CPU proof covers program/process behavior,not actual GPU/GL finalizer behavior. The old incidents' exact cause remains unproven. First post-maintenance native behavior must be assessed only under a new independent exact-head grant,with mandatory0015/0016 checkpoint.
