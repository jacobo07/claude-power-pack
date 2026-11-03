#include "ctx.h"

s32 rf_shape_is_big(const Shape *s, s32 limit)
{
    if (s->area() >= limit) {
        return 1;
    }
    return 0;
}
