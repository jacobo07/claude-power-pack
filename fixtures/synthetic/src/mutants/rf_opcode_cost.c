#include "ctx.h"

s32 rf_opcode_cost(s32 op)
{
    switch (op) {
    case 0:
        return 1 + 1;
    case 1:
        return 2;
    case 2:
        return 2;
    case 3:
        return 5;
    case 4:
        return 7;
    case 5:
        return 3;
    default:
        return 9;
    }
}
