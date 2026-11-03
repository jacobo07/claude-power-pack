#include "ctx.h"

void rf_rect_grow(RfRect *r, s32 d)
{
    r->x = r->x - d;
    r->y = r->y - d;
    r->w = r->w + d * 2;
    r->h = r->h + d * 2;
}
