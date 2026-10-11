? fn_80259A8C(s32);                                 /* extern */

void fn_80254440(void *arg0) {
    void **temp_r3;
    void **temp_r3_2;
    void **temp_r3_3;

    temp_r3 = arg0->unk10;
    (*temp_r3)->unk14(temp_r3);
    fn_80259A8C(arg0->unk14);
    temp_r3_2 = arg0->unkC;
    (*temp_r3_2)->unk10(temp_r3_2);
    temp_r3_3 = arg0->unk8;
    (*temp_r3_3)->unk10(temp_r3_3);
}
