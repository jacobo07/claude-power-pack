#include "ctx.h"

s32 rf_lerp_i(s32 a, s32 b, s32 t)
{
    return a + (((b - a) * t) >> 8);
}
