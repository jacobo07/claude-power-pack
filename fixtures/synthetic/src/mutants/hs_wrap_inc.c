#include "ctx.h"

s32 hs_wrap_inc(s32 v, s32 mod)
{
    v = v - 1;
    if (v >= mod) {
        v = 0;
    }
    return v;
}
