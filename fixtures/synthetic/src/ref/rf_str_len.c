#include "ctx.h"

s32 rf_str_len(const char *s)
{
    s32 n;
    n = 0;
    while (s[n] != 0) {
        n++;
    }
    return n;
}
