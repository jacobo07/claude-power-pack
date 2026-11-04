#include "ctx.h"

s32 rf_find_first(const s32 *a, s32 n, s32 key)
{
    s32 i;
    for (i = 0; i < n; i++) {
        if (a[i] == key) {
            return i;
        }
    }
    return -1;
}
