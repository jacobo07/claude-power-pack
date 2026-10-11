void *fn_800B4508(?, ? *);                          /* extern */
s32 fn_800B4524(?);                                 /* extern */
void fn_801F3374(void); /* extern */
void fn_802773E4(void); /* extern */
? fn_8027990C(void *);                              /* extern */
void *fn_80279A08(s32);                             /* extern */
void *fn_80279E44();                                /* extern */
extern ? lbl_80419CF0;
extern ? lbl_80419CFC;

void *fn_802797E4(void *arg0) {
    s32 var_r29;
    s32 var_r30;
    s32 var_r4;
    s32 var_r6;
    void *temp_r3;
    void *temp_r3_2;
    void *temp_r5;
    void *var_r3;
    void *var_r3_2;
    void *var_r3_3;

    fn_802773E4();
    arg0->unk0 = &lbl_80419CFC;
    temp_r3 = fn_800B4508(0x14, &lbl_80419CFC);
    if (temp_r3 != NULL) {
        fn_801F3374();
        temp_r3->unk0 = &lbl_80419CF0;
        temp_r3->unk8 = 4;
        temp_r3->unk4 = fn_800B4524(0x10);
        var_r29 = temp_r3->unk8 - 1;
        var_r30 = var_r29 * 4;
        do {
            var_r3 = fn_800B4508(0x38);
            if (var_r3 != NULL) {
                var_r3 = fn_80279E44();
            }
            var_r29 -= 1;
            *(temp_r3->unk4 + var_r30) = var_r3;
            var_r30 -= 4;
        } while (var_r29 >= 0);
        var_r3_2 = fn_800B4508(0x28);
        if (var_r3_2 != NULL) {
            var_r3_2 = fn_80279A08(temp_r3->unk8);
        }
        temp_r3->unkC = var_r3_2;
        var_r3_3 = fn_800B4508(0x28);
        if (var_r3_3 != NULL) {
            var_r3_3 = fn_80279A08(temp_r3->unk8);
        }
        temp_r3->unk10 = var_r3_3;
        fn_8027990C(temp_r3);
    }
    arg0->unk8 = temp_r3;
    var_r6 = 3;
    var_r4 = 0xC;
    do {
        temp_r5 = arg0->unk8;
        var_r6 -= 1;
        temp_r3_2 = *(temp_r5->unk4 + var_r4);
        var_r4 -= 4;
        temp_r3_2->unk2C = temp_r5;
    } while (var_r6 >= 0);
    return arg0;
}
