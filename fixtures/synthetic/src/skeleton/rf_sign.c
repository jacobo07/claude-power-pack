#include "ctx.h"

s32 rf_sign(s32 v)
{
    if (0 > v) {
        return -1;
    }
    if (v > 0) {
        return 1;
    }
    {
        s32 rv;
        rv = 0;
        return rv;
    }
}
