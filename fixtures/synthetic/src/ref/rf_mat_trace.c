#include "ctx.h"

s32 rf_mat_trace(const s32 *m, s32 n)
{
    s32 i;
    s32 s;
    s = 0;
    for (i = 0; i < n; i++) {
        s = s + m[i * n + i];
    }
    return s;
}
