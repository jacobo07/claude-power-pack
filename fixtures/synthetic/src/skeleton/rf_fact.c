#include "ctx.h"

s32 rf_fact(s32 n)
{
    s32 r;
    r = 1;
    while (n > 1) {
        r = n * r;
        n = n - 1;
    }
    {
        s32 rv;
        rv = r;
        return rv;
    }
}
