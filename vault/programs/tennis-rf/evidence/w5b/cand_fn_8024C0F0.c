? fn_800076F0(? *, ? **, ? *);                      /* extern */
void fn_800B4548(s32); /* extern */
void fn_800BD138(s32, s32); /* extern */
extern ? lbl_80418A00;
extern ? lbl_804F96B8;

? **fn_8024C0F0(? **arg0, s32 arg1) {
    if (arg0 != NULL) {
        *arg0 = &lbl_80418A00;
        fn_800076F0(&lbl_804F96B8, arg0, &lbl_804F96B8);
        fn_800BD138(arg0, 0);
        if (arg1 > 0) {
            fn_800B4548(arg0);
        }
    }
    return arg0;
}
