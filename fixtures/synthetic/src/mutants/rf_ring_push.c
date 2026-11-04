#include "ctx.h"

void rf_ring_push(s32 v)
{
    rf_ring[rf_ring_head & 15] = v;
    rf_ring_head = rf_ring_head - 1;
}
