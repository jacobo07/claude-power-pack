#include "ctx.h"

f32 rf_flt_clamp(f32 v, f32 lo, f32 hi)
{
    if (lo > v) {
        return lo;
    }
    if (hi < v) {
        return hi;
    }
    return v;
}
