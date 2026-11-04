#include "ctx.h"

s32 rf_counter_next(void)
{
    rf_counter = 1 + rf_counter;
    {
        s32 rv;
        rv = rf_counter;
        return rv;
    }
}
