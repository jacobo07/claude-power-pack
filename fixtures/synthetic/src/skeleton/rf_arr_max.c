#include "ctx.h"

s32 rf_arr_max(const s32 *a, s32 n)
{
    s32 i;
    s32 m;
    m = a[0];
    for (i = 1; n > i; i++) {
        if (m < a[i]) {
            m = a[i];
        }
    }
    return m;
}
