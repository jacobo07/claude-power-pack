#include "ctx.h"

s32 hs_total_scaled(Shape *a, Shape *b, s32 k)
{
    {
        s32 rv;
        rv = ((s32 (*)(Shape*, s32))(*(void ***)a)[1])(a, k) + b->scale(k);
        return rv;
    }
}
