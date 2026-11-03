#include "ctx.h"

void rf_rect_grow(RfRect *r, s32 d)
{
    r->x = r->x - d;
    r->y = r->y - d;
    r->w = d + r->w * 2;
    r->h = d + r->h * 2;
}
