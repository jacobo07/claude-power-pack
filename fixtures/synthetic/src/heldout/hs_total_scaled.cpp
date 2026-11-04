#include "ctx.h"

s32 hs_total_scaled(Shape *a, Shape *b, s32 k)
{
    return a->scale(k) + b->scale(k);
}
