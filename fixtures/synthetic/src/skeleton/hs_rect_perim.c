#include "ctx.h"

s32 hs_rect_perim(const RfRect *r)
{
    return (r->h + r->w) * 2;
}
