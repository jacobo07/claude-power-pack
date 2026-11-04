#include "ctx.h"

s32 rf_bsearch(const s32 *a, s32 n, s32 key)
{
    s32 hi;
    s32 lo;
    s32 mid;
    lo = 0;
    hi = n - 1;
    while (lo <= hi) {
        mid = (hi + lo) / 2;
        if (a[mid] == key) {
            return mid;
        }
        if (a[mid] < key) {
            lo = mid + 1;
        } else {
            hi = mid - 1;
        }
    }
    return -1;
}
