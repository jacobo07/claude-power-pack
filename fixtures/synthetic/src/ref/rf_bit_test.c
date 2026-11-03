#include "ctx.h"

s32 rf_bit_test(const u32 *bits, u32 idx)
{
    return (bits[idx >> 5] >> (idx & 31)) & 1;
}
