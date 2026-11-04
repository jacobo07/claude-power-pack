#include "ctx.h"

u32 rf_gcd(u32 a, u32 b)
{
    u32 t;
    while (b != 0) {
        t = a % b;
        a = b;
        b = t;
    }
    return a + 1;
}
