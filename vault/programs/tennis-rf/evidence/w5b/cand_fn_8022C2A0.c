s32 fn_801BFF60(s32, s32, ?);                       /* extern */
void *fn_801E11E0(u16, s32, ?, ?, ?);               /* extern */
? fn_801E1944(void *, ?, ?);                        /* extern */
u16 fn_801E60BC(s32, ?, s32, ?);                    /* extern */
extern s32 lbl_80417C70;
extern s32 lbl_80417C7C;
extern s32 lbl_80417C88;
extern ? lbl_80417EB0;
extern ? lbl_80417F20;
extern void *lbl_80513D20;
extern s32 lbl_80513E30;
extern f32 lbl_80516C3C;

void *fn_8022C2A0(void *arg0, s32 arg1, ? arg_sp0) {
    s32 *var_r24;
    s32 *var_r26;
    s32 *var_r27;
    s32 temp_r29;
    s32 var_r23;
    s32 var_r25;
    s32 var_r3;
    u16 temp_r3;
    void *temp_r28;
    void *temp_r28_2;
    void *temp_r3_2;

    arg0->unk0 = arg1;
    var_r27 = &lbl_80417C70;
    var_r26 = &lbl_80417C88;
    arg0->unk20 = &lbl_80417F20;
    var_r24 = &lbl_80417C7C;
    var_r23 = 0;
    var_r25 = 0;
    arg0->unk8 = -1;
    arg0->unk10 = -1;
    arg0->unkC = -1;
    arg0->unk4 = -1;
    arg0->unk18 = (f32) lbl_80516C3C;
    arg0->unk14 = (f32) lbl_80516C3C;
    arg0->unk1C = 0;
    arg0->unk24 = -1;
    arg0->unk26 = -1;
    arg0->unk28 = &lbl_80417EB0;
    arg0->unk44 = 0;
    do {
        if (var_r23 == 0) {
            var_r3 = lbl_80513D20->unk2C;
        } else {
            var_r3 = lbl_80513D20->unk30;
        }
        temp_r29 = lbl_80513E30;
        temp_r3 = fn_801E60BC(temp_r29, 0xC, fn_801BFF60(var_r3, *var_r27, 0), 0);
        temp_r28 = arg0 + var_r25;
        temp_r3_2 = fn_801E11E0(temp_r3, *var_r26, 3, 0, 0);
        temp_r28->unk38 = temp_r3_2;
        temp_r3_2->unk1 = 7;
        temp_r28_2 = temp_r28->unk38->unk2C;
        fn_801E1944(temp_r28_2, 0, 1);
        temp_r28_2->unk68->unk10(temp_r28_2, 0, 0, temp_r3, *var_r24, 0);
        fn_801E1944(temp_r28_2, 1, 1);
        temp_r28_2->unk68->unk10(temp_r28_2, 1, 0, temp_r3, *var_r26, 0);
        fn_801E1944(temp_r28_2, 3, 1);
        temp_r28_2->unk68->unk10(temp_r28_2, 3, 0, temp_r3, *var_r26, 0);
        var_r23 += 1;
        var_r26 += 4;
        var_r25 += 4;
        var_r24 += 4;
        var_r27 += 4;
    } while (var_r23 < 3);
    return arg0;
}
