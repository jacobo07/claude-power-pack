#include "ctx.h"

s32 rf_clamp(s32 v, s32 lo, s32 hi)
{
    if (lo > v) {
        return lo;
    }
    if (hi < v) {
        return hi;
    }
    return v;
}
