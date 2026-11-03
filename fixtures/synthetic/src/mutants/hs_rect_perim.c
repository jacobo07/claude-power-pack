#include "ctx.h"

s32 hs_rect_perim(const RfRect *r)
{
    return (r->w - r->h) * 2;
}
