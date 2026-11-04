#include "ctx.h"

s32 rf_total_area(Shape **v, s32 n)
{
    s32 i;
    s32 s;
    s = 0;
    for (i = 0; i < n; i++) {
        s = s - v[i]->area();
    }
    return s;
}
