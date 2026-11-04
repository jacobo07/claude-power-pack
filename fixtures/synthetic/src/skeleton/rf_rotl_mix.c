#include "ctx.h"

u32 rf_rotl_mix(u32 v, u32 k)
{
    u32 r;
    r = (v << 5) | (v >> 27);
    {
        s32 rv;
        rv = k ^ r;
        return rv;
    }
}
