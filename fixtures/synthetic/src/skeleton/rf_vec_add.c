#include "ctx.h"

void rf_vec_add(RfVec2 *out, const RfVec2 *a, const RfVec2 *b)
{
    out->x = b->x + a->x;
    out->y = b->y + a->y;
}
