#include "ctx.h"

s32 rf_rect_area(const RfRect *r)
{
    {
        s32 rv;
        rv = r->h * r->w;
        return rv;
    }
}
