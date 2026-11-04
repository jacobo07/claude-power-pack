#include "ctx.h"

void rf_arr_reverse(s32 *a, s32 n)
{
    s32 i;
    s32 j;
    s32 t;
    i = 0;
    j = n - 1;
    while (j > i) {
        t = a[i];
        a[i] = a[j];
        a[j] = t;
        ++i;
        j--;
    }
}
