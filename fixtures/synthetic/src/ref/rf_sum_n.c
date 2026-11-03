#include "ctx.h"

s32 rf_sum_n(s32 n)
{
    s32 i;
    s32 s;
    s = 0;
    for (i = 1; i <= n; i++) {
        s = s + i;
    }
    return s;
}
