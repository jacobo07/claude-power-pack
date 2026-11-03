#include "ctx.h"

s32 rf_state_next(s32 st, s32 ev)
{
    switch (st) {
    case 0:
        if (ev == 1) {
            return 1;
        }
        return 0;
    case 1:
        if (ev == 2) {
            return 2;
        }
        return 0;
    case 2:
        return 3;
    default:
        return 0;
    }
}
