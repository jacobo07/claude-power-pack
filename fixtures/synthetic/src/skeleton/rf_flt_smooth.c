#include "ctx.h"

f32 rf_flt_smooth(f32 prev, f32 cur)
{
    return cur * prev + rf_flt_half * rf_flt_half;
}
