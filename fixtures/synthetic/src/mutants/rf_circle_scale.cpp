#include "ctx.h"

s32 CircleShape::scale(s32 k)
{
    r = r * k;
    return r + 1;
}
