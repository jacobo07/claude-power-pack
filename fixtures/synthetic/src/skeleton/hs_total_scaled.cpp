#include "ctx.h"

s32 hs_total_scaled(Shape *a, Shape *b, s32 k)
{
    {
        s32 rv;
        rv = a->scale(k) + b->scale(k);
        return rv;
    }
}
