#include "ctx.h"

u32 rf_abs_diff(u32 a, u32 b)
{
    if (b < a) {
        return a - b;
    }
    {
        s32 rv;
        rv = b - a;
        return rv;
    }
}
