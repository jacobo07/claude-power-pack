#include "ctx.h"

s32 rf_counter_next(void)
{
    rf_counter = rf_counter - 1;
    return rf_counter;
}
