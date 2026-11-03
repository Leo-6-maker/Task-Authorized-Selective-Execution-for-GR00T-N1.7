"""CPU-only shared-device admission; never changes policy or simulation inputs.

Nine GiB leaves a seven GiB allocator budget after the existing two GiB
reserve. The prior pinned E2 server's recorded maximum reserved allocation
was 6,482,296,832 bytes. This is an engineering admission estimate, not a
guarantee of GPU1 execution; real allocation failures remain fatal.
"""

GIB = 1024 ** 3
MINIMUM_FREE_BYTES = 9 * GIB
RESERVED_FREE_BYTES = 2 * GIB
MAXIMUM_PROCESS_FRACTION = 0.55


def require_free_memory(free_bytes):
    if type(free_bytes) is not int or free_bytes < MINIMUM_FREE_BYTES:
        raise ValueError('less than 9 GiB free VRAM; do not affect other tasks')


def allocator_fraction(free_bytes, total_bytes):
    require_free_memory(free_bytes)
    if type(total_bytes) is not int or total_bytes < free_bytes:
        raise ValueError('invalid GPU free/total memory inventory')
    # Identical to the original allocator rule. Neither the 55% cap nor the
    # two GiB reserve may be overridden by CLI/environment/resource receipts.
    return min(MAXIMUM_PROCESS_FRACTION,
               (free_bytes - RESERVED_FREE_BYTES) / total_bytes)
