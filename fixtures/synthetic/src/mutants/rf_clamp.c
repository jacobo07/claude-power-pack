#include "ctx.h"

s32 rf_clamp(s32 v, s32 lo, s32 hi)
{
    if (v <= lo) {
        return lo;
    }
    if (v > hi) {
        return hi;
    }
    return v;
}
