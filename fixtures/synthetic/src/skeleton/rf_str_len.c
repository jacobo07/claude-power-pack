#include "ctx.h"

s32 rf_str_len(const char *s)
{
    s32 n;
    n = 0;
    while (0 != s[n]) {
        n++;
    }
    {
        s32 rv;
        rv = n;
        return rv;
    }
}
