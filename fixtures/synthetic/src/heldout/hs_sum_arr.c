#include "ctx.h"

s32 hs_sum_arr(const s32 *a, s32 n)
{
    s32 i;
    s32 s;
    s = 0;
    for (i = 0; i < n; i++) {
        s = s + a[i];
    }
    return s;
}
