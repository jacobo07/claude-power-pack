#include "ctx.h"

void rf_vec_add(RfVec2 *out, const RfVec2 *a, const RfVec2 *b)
{
    out->x = a->x + b->x;
    out->y = a->y + b->y;
}
