#include "ctx.h"

s32 rf_node_sum(const RfNode *n)
{
    s32 s;
    s = 0;
    while (n != 0) {
        s = n->value + s;
        n = n->next;
    }
    {
        s32 rv;
        rv = s;
        return rv;
    }
}
