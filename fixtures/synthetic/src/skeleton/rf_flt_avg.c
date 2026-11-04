#include "ctx.h"

f32 rf_flt_avg(const f32 *a, s32 n)
{
    f32 s;
    s32 i;
    s = 0.0f;
    for (i = 0; n > i; i++) {
        s = a[i] + s;
    }
    return s / (f32)n;
}
