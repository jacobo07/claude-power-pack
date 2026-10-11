? fn_80097048(void *);                              /* extern */
void *fn_800973B4();                                /* extern */
? fn_8009746C(void *, s32);                         /* extern */
? fn_80097FE4(void *, u16, u16, ?, ?);              /* extern */
s32 fn_80098AF8(void *);                            /* extern */
void fn_80099DE4(s32, s32, s32); /* extern */
? fn_8009BCC0(?, ? *, s32 *);                       /* extern */
? fn_800AAFE4(s32 *, void *);                       /* extern */
? fn_800AB0C4(s32 *);                               /* extern */
void *fn_800AB810(void *);                          /* extern */
void fn_80100460(void); /* extern */
? fn_80108080(? *, s32, f32, f32, f32);             /* extern */
extern ? lbl_803DB7A0;
extern s32 lbl_805122F4;
extern void *lbl_80513DD8;
extern s32 lbl_80513E40;
extern u8 lbl_80513E45;
extern void *lbl_80513E4C;
extern s32 lbl_80514F64;
extern f32 lbl_80516C3C;
extern f32 lbl_80516C40;

void fn_8022D46C(void *arg0, ? arg_sp0) {
    u16 sp74;
    f32 sp5C;
    f32 sp58;
    s32 sp44;
    s32 sp40;
    ? sp10;
    s32 sp8;
    s16 temp_r27_2;
    s16 temp_r28;
    s16 var_r28;
    s16 var_r28_3;
    s32 temp_r5_2;
    s32 var_ctr;
    s32 var_ctr_2;
    s32 var_ctr_3;
    s32 var_r28_2;
    s32 var_r5;
    s32 var_r6;
    s32 var_r6_2;
    void *temp_r27;
    void *temp_r3;
    void *temp_r3_10;
    void *temp_r3_2;
    void *temp_r3_3;
    void *temp_r3_4;
    void *temp_r3_5;
    void *temp_r3_6;
    void *temp_r3_7;
    void *temp_r3_8;
    void *temp_r3_9;
    void *temp_r4;
    void *temp_r5;
    void *temp_r5_3;
    void *var_r27;
    void *var_r27_2;
    void *var_r27_3;
    void *var_r28_4;

    temp_r3 = arg0->unk4C;
    temp_r3->unk28->unk14(temp_r3);
    temp_r3_2 = arg0->unk50;
    temp_r3_2->unk28->unk14(temp_r3_2);
    temp_r3_3 = arg0->unk54;
    if (temp_r3_3 != NULL) {
        temp_r3_3->unk28->unk14();
    }
    if ((s32) lbl_805122F4 == 1) {
        var_r28 = *(&lbl_803DB7A0 + (arg0->unk0 * 2));
        var_r27 = arg0 + (var_r28 * 4);
loop_5:
        if (var_r28 <= (s16) *(&lbl_803DB7A0 + 0xC + (arg0->unk0 * 2))) {
            temp_r3_4 = var_r27->unk58;
            temp_r3_4->unk28->unk18(temp_r3_4);
            var_r27 += 4;
            var_r28 += 1;
            goto loop_5;
        }
        var_r27_2 = arg0;
        var_r28_2 = 0;
        do {
            temp_r3_5 = var_r27_2->unk58;
            temp_r3_5->unk28->unk18(temp_r3_5);
            var_r28_2 += 1;
            var_r27_2 += 4;
        } while (var_r28_2 <= 3);
        var_r28_3 = *(&lbl_803DB7A0 + 0x18 + (arg0->unk0 * 2));
        var_r27_3 = arg0 + (var_r28_3 * 4);
loop_10:
        if (var_r28_3 <= (s16) *(&lbl_803DB7A0 + 0x24 + (arg0->unk0 * 2))) {
            temp_r3_6 = var_r27_3->unkA0;
            temp_r3_6->unk28->unk18(temp_r3_6);
            var_r27_3 += 4;
            var_r28_3 += 1;
            goto loop_10;
        }
        temp_r3_7 = arg0->unkA8;
        if (temp_r3_7 != NULL) {
            temp_r3_7->unk28->unk18();
        }
    } else if ((s32) lbl_805122F4 == 0) {
        if ((s32) lbl_80513DD8->unkB != 0) {
            if ((s32) arg0->unkB0 == 0) {
                arg0->unkAC = 0;
                var_r5 = 0;
                var_ctr = 0x1F;
                do {
                    temp_r4 = (lbl_80513E40 + ((var_r5 * 4) & 0x3FC))->unk14;
                    if ((temp_r4 != NULL) && (temp_r4->unk4 & 1)) {
                        arg0->unkAC = (s32) (arg0->unkAC | (1 << var_r5));
                    }
                    var_r5 += 1;
                    var_ctr -= 1;
                } while (var_ctr != 0);
                return;
            }
            var_r6 = 0;
            var_ctr_2 = 0x1F;
            do {
                temp_r5 = (lbl_80513E40 + ((var_r6 * 4) & 0x3FC))->unk14;
                if ((temp_r5 != NULL) && (arg0->unkAC & (1 << var_r6))) {
                    temp_r5->unk4 = (u16) (temp_r5->unk4 & 0xFFFE);
                }
                var_r6 += 1;
                var_ctr_2 -= 1;
            } while (var_ctr_2 != 0);
            return;
        }
        if ((s32) arg0->unkB0 != 0) {
            arg0->unkB0 = 0U;
            fn_80097048(arg0->unkB4);
            arg0->unkB4 = NULL;
        }
    } else if ((u8) lbl_80513E45 == 0x1F) {
        switch ((s32) lbl_805122F4) {               /* irregular */
        case 2:
            if ((s32) lbl_80513DD8->unkB != 0) {
                temp_r27 = lbl_80513E4C;
                if ((s32) arg0->unkB0 == 0) {
                    arg0->unkB0 = 1U;
                    temp_r3_8 = fn_800AB810(temp_r27);
                    temp_r28 = (s16) temp_r3_8->unk8;
                    temp_r27_2 = (s16) temp_r3_8->unkC;
                    if (((u16) temp_r28 == 0) || ((u16) temp_r27_2 == 0)) {
                        var_r28_4 = NULL;
                    } else {
                        temp_r3_9 = fn_800973B4();
                        temp_r3_9->unk2 = temp_r28;
                        var_r28_4 = temp_r3_9;
                        temp_r3_9->unk4 = temp_r27_2;
                        temp_r3_9->unk6 = 6;
                        temp_r3_9->unk14->unkC();
                        var_r28_4->unk7 = 0;
                        var_r28_4->unk8 = 0;
                        var_r28_4->unk9 = 1;
                        var_r28_4->unkA = 1;
                        fn_8009746C(var_r28_4, fn_80098AF8(var_r28_4));
                    }
                    arg0->unkB4 = var_r28_4;
                    fn_80097FE4(var_r28_4, (u16) (s32) temp_r3_8->unk0, (u16) (s32) temp_r3_8->unk4, 0, -1);
                    return;
                }
                fn_800AAFE4(&sp40, temp_r27);
                sp58 = lbl_80516C3C;
                sp5C = lbl_80516C40;
                if (sp44 != 1) {
                    sp44 = 1;
                    sp74 |= 1;
                }
                sp40 = 0;
                fn_800AB0C4(&sp40);
                fn_80099DE4(1, 1, 1);
                fn_80100460();
                temp_r3_10 = arg0->unkB4;
                temp_r3_10->unk14->unk14(temp_r3_10, 0);
                temp_r5_2 = (s32) temp_r27->unk8;
                fn_80108080(&sp10, temp_r5_2, (f32) (u16) temp_r5_2, (f32) (u16) (s32) temp_r27->unkC, lbl_80516C40);
                sp8 = lbl_80514F64;
                fn_8009BCC0(0x10, &sp10, &sp8);
                return;
            }
            break;
        case 3:
            if ((s32) arg0->unkB0 != 0) {
                var_r6_2 = 0;
                var_ctr_3 = 0x1F;
                do {
                    temp_r5_3 = (lbl_80513E40 + ((var_r6_2 * 4) & 0x3FC))->unk14;
                    if ((temp_r5_3 != NULL) && (arg0->unkAC & (1 << var_r6_2))) {
                        temp_r5_3->unk4 = (u16) (temp_r5_3->unk4 | 1);
                    }
                    var_r6_2 += 1;
                    var_ctr_3 -= 1;
                } while (var_ctr_3 != 0);
            }
            break;
        }
    }
}
