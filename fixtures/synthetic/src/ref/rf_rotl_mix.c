#include "ctx.h"

u32 rf_rotl_mix(u32 v, u32 k)
{
    u32 r;
    r = (v << 5) | (v >> 27);
    return r ^ k;
}
