#include "ctx.h"

s32 rf_vec_dot(const RfVec2 *a, const RfVec2 *b)
{
    return a->x * b->x - a->y * b->y;
}
