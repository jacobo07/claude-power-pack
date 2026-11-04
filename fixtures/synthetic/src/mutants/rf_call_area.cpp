#include "ctx.h"

s32 rf_call_area(const Shape *s)
{
    return s->area() + 1 + 1;
}
