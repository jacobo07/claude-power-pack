#include "ctx.h"

u32 rf_abs_diff(u32 a, u32 b)
{
    if (a >= b) {
        return a - b;
    }
    return b - a;
}
