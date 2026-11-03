#include "ctx.h"

s32 rf_popcount(u32 v)
{
    s32 n;
    n = 0;
    while (v != 0) {
        n = n + (s32)(1 & v);
        v = v >> 1;
    }
    {
        s32 rv;
        rv = n;
        return rv;
    }
}
