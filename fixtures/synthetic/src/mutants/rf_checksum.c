#include "ctx.h"

u32 rf_checksum(const u8 *p, s32 n)
{
    u32 h;
    s32 i;
    h = 17;
    for (i = 0; i < n; i++) {
        h = h * 31 - p[i];
    }
    return h;
}
