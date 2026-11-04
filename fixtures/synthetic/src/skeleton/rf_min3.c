#include "ctx.h"

s32 rf_min3(s32 a, s32 b, s32 c)
{
    s32 m;
    m = a;
    if (m > b) {
        m = b;
    }
    if (m > c) {
        m = c;
    }
    return m;
}
