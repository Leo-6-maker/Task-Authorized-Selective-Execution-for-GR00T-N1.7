# Original cleanup incidents: known and unknown chronology

The old runtime is `a1c6424bd348b36c55a20d38750a269e9551a698`. Both failed IDs remain consumed and unchanged. The bound original hashes are in the reviewed PR19 manifest/receipt origins and the two verified original backups. Structured known timestamps appear in incident_timeline.json.

| Original ID | Main controls | Calls / ACCEPT | Saved task-success | Native exit | Worker final exit | Frozen outcome |
| --- | ---: | ---: | --- | ---: | ---: | --- |
|0010|120|15|true|1|0|CLEANUP_ERROR,unknown |
|0014|148|19|true|1|0|CLEANUP_ERROR,unknown |

The last control-attempt timestamp records entry into the final main control,not its return or a worker close boundary. The result completion timestamp includes cleanup. Neither original logs an exact close-send,worker-receive,native-finalizer-start/end,join-return,liveness-check,terminate-syscall or exit-reap timestamp. Those times remain UNKNOWN; no subtraction of fixed10s/5s is used to invent them.

Both original cleanup stacks identify the `Shadow.close` branch after join10:request terminate,join5,raise. Final worker0 does not prove when a signal reached the worker or whether the native finalizer had returned at the first liveness observation. Scheduling race and delayed finalization remain hypotheses. No GPU/MuJoCo/policy reproduction occurred in Issue20.

The new CPU protocol tests the relevant classes using genuine spawn workers:completed native finalizer followed by process exit beyond the old10s boundary,missing/partial messages,backpressure,finalizer exceptions,nonzero exits,TERM/KILL and repeated close. New receipt fields distinguish native completion,observed actual exit,force requests and parent resource release. Force-event flags record parent requests; actual delivery must be assessed with genuine exit/signal receipts. Old files never receive these new fields.
