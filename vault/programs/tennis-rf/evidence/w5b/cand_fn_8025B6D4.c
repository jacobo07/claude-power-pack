f32 fn_801088B0(void *);                            /* extern */
? fn_8024DF0C(void *, void *, ?);                   /* extern */
s32 fn_80253D58();                                  /* extern */
s32 fn_8025A674(void *);                            /* extern */
? fn_8025A758(?, void *);                           /* extern */
? fn_802636E0(s32, void *);                         /* extern */
extern void *lbl_80513F98;
extern f32 lbl_8051721C;
extern f32 lbl_80517220;
extern f32 lbl_805172A8;

void fn_8025B6D4(void *arg0) {
    f32 temp_f1;
    s32 temp_r0;
    s32 temp_r3_3;
    s32 temp_r3_4;
    void *temp_r31;
    void *temp_r3;
    void *temp_r3_2;
    void *temp_r5;

    temp_r5 = lbl_80513F98->unk24;
    temp_r31 = temp_r5->unk1A0;
    fn_8025A758(1, temp_r5);
    temp_r3 = arg0->unk1AC;
    temp_r3->unk0 = (f32) arg0->unk8;
    temp_r3->unk4 = (f32) arg0->unkC;
    temp_r3->unk8 = (f32) arg0->unk10;
    temp_r3_2 = arg0->unk1AC + 0xC;
    arg0->unk1AC = temp_r3_2;
    if (temp_r3_2 > (void *) (arg0 + 0x1A0)) {
        arg0->unk1AC = (void *) (arg0 + 0x44);
    }
    temp_f1 = fn_801088B0(arg0 + 0x1B8) / lbl_805172A8;
    arg0->unk1D8 = temp_f1;
    if (temp_f1 > lbl_80517220) {
        arg0->unk1D8 = (f32) lbl_80517220;
    } else if (temp_f1 < lbl_8051721C) {
        arg0->unk1D8 = (f32) lbl_8051721C;
    }
    if (arg0->unk1E4 & 0xC) {
        if ((s32) arg0->unk1C4 == 1) {
            fn_8024DF0C(lbl_80513F98->unk24->unk1A0, arg0, 0xA);
            fn_802636E0(lbl_80513F98->unk1C, arg0);
            return;
        }
        if ((s32) arg0->unk1CC == 0) {
            temp_r3_3 = fn_8025A674(arg0);
            if (temp_r3_3 & 2) {
                if ((s32) arg0->unk1C4 == 2) {
                    fn_8024DF0C(temp_r31, arg0, 3);
                } else {
                    fn_8024DF0C(temp_r31, arg0, 0);
                }
            } else if (((s32) arg0->unk1DC != 0) && ((s32) ((temp_r3_3 & 1) ^ fn_80253D58() ^ 1) != 0)) {
                if ((s32) arg0->unk1C4 == 2) {
                    fn_8024DF0C(temp_r31, arg0, 3);
                } else {
                    fn_8024DF0C(temp_r31, arg0, 1);
                }
            } else if ((s32) arg0->unk1C4 == 2) {
                temp_r3_4 = temp_r31->unkC;
                if (((temp_r3_4 == 0) && !(temp_r3_3 & 8)) || ((temp_r3_4 == 1) && !(temp_r3_3 & 4))) {
                    fn_8024DF0C(temp_r31, arg0, 3);
                } else if (arg0->unk1E4 & 2) {
                    fn_8024DF0C(temp_r31, arg0, 4);
                }
            } else {
                fn_8024DF0C(temp_r31, arg0, 5);
            }
        }
        temp_r0 = arg0->unk1CC + 1;
        arg0->unk1CC = temp_r0;
        if (temp_r0 == 2) {
            fn_8024DF0C(temp_r31, arg0, 2);
            arg0->unk1C8 = (s32) (arg0->unk1C8 & 0xFFFFFFFB);
        }
    }
}
