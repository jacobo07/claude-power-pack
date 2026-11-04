#include "ctx.h"

f32 rf_flt_lerp(f32 a, f32 b, f32 t)
{
    return a + (b - a) * t;
}
