#include "ctx.h"

s32 rf_str_eq(const char *a, const char *b)
{
    while (*a != 0 && *a == *b) {
        ++a;
        b++;
    }
    {
        s32 rv;
        rv = *a == *b;
        return rv;
    }
}
