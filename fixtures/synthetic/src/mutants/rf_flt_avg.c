#include "ctx.h"

f32 rf_flt_avg(const f32 *a, s32 n)
{
    f32 s;
    s32 i;
    s = 0.0f;
    for (i = 0; i < n; i++) {
        s = s - a[i];
    }
    return s / (f32)n;
}
