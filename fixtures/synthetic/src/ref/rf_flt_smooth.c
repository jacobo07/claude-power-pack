#include "ctx.h"

f32 rf_flt_smooth(f32 prev, f32 cur)
{
    return prev * rf_flt_half + cur * rf_flt_half;
}
