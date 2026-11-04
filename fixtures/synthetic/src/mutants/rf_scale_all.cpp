#include "ctx.h"

void rf_scale_all(Shape **v, s32 n, s32 k)
{
    s32 i;
    for (i = 0; i <= n; i++) {
        rf_sink = v[i]->scale(k);
    }
}
