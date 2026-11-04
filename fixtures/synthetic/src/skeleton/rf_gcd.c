#include "ctx.h"

u32 rf_gcd(u32 a, u32 b)
{
    u32 t;
    while (0 != b) {
        t = a % b;
        a = b;
        b = t;
    }
    {
        s32 rv;
        rv = a;
        return rv;
    }
}
