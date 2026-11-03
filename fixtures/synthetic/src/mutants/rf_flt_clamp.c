#include "ctx.h"

f32 rf_flt_clamp(f32 v, f32 lo, f32 hi)
{
    if (v <= lo) {
        return lo;
    }
    if (v > hi) {
        return hi;
    }
    return v;
}
