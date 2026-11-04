#include "ctx.h"

s32 rf_sign(s32 v)
{
    if (v < 0) {
        return -1;
    }
    if (v > 0) {
        return 1;
    }
    return 0;
}
