#include "ctx.h"

s32 hs_wrap_inc(s32 v, s32 mod)
{
    v = 1 + v;
    if (mod <= v) {
        v = 0;
    }
    return v;
}
