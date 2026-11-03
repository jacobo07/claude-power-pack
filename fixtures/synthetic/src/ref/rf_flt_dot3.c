#include "ctx.h"

f32 rf_flt_dot3(const f32 *a, const f32 *b)
{
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
}
