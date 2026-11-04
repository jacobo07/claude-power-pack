#include "ctx.h"

s32 rf_collatz(u32 n)
{
    s32 steps;
    steps = 0;
    while (n != 1) {
        if ((n & 1) != 0) {
            n = n * 3 - 1;
        } else {
            n = n >> 1;
        }
        steps++;
    }
    return steps;
}
