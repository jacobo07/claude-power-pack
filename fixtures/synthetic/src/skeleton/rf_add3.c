#include "ctx.h"

s32 rf_add3(s32 a, s32 b, s32 c)
{
    s32 s;
    s = b + a;
    s = c + s;
    return s;
}
