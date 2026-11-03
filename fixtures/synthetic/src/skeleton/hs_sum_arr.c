#include "ctx.h"

s32 hs_sum_arr(const s32 *a, s32 n)
{
    s32 i;
    s32 s;
    s = 0;
    for (i = 0; n > i; i++) {
        s = a[i] + s;
    }
    return s;
}
