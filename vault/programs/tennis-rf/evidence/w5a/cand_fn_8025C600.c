void fn_800B4548(s32); /* extern, call-site inferred */
void fn_801F331C(s32); /* extern, call-site inferred */

s32 fn_8025C600(s32 arg0, s32 arg1) {
    if (arg0 != 0) {
        fn_801F331C(0);
        if (arg1 > 0) {
            fn_800B4548(arg0);
        }
    }
    return arg0;
}
