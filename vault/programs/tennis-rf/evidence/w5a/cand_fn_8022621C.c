void fn_800B4548(s32); /* extern, call-site inferred */
void fn_800BC298(s32); /* extern, call-site inferred */

s32 fn_8022621C(s32 arg0, s32 arg1) {
    s32 temp_cr0_eq;

    temp_cr0_eq = arg0 == 0;
    if (temp_cr0_eq == 0) {
        if (temp_cr0_eq == 0) {
            fn_800BC298(0);
        }
        if (arg1 > 0) {
            fn_800B4548(arg0);
        }
    }
    return arg0;
}
