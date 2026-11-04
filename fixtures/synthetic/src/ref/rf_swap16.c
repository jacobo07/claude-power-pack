#include "ctx.h"

u16 rf_swap16(u16 v)
{
    return (u16)((v << 8) | (v >> 8));
}
