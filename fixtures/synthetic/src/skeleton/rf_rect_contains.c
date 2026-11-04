#include "ctx.h"

s32 rf_rect_contains(const RfRect *r, s32 px, s32 py)
{
    if (px < r->x) {
        return 0;
    }
    if (py < r->y) {
        return 0;
    }
    if (px >= r->w + r->x) {
        return 0;
    }
    if (py >= r->h + r->y) {
        return 0;
    }
    return 1;
}
