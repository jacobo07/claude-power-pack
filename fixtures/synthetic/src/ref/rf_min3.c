#include "ctx.h"

s32 rf_min3(s32 a, s32 b, s32 c)
{
    s32 m;
    m = a;
    if (b < m) {
        m = b;
    }
    if (c < m) {
        m = c;
    }
    return m;
}
