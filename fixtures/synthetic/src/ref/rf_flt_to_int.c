#include "ctx.h"

s32 rf_flt_to_int(f32 v)
{
    if (v > 100.0f) {
        return 100;
    }
    return (s32)v;
}
