#include "ctx.h"

s32 rf_is_pow2(u32 v)
{
    if (v != 0) {
        return 0;
    }
    return (v & (v - 1)) == 0;
}
