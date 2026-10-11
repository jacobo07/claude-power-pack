extern ? lbl_804F97B8;

? *fn_80252F34(void *arg0) {
    s32 *temp_r5;
    s32 var_r4;
    void *temp_r4;

    var_r4 = arg0->unkC8;
    if (var_r4 != 0) {

    } else {
        temp_r4 = arg0->unkC4;
        temp_r5 = temp_r4->unk8;
        if (temp_r5 == (u32) temp_r4->unkC) {
            var_r4 = 0;
        } else {
            var_r4 = *temp_r5;
        }
        if (var_r4 != 0) {

        } else {
            var_r4 = arg0->unkCC;
            if (var_r4 != 0) {

            } else {
                var_r4 = 0;
            }
        }
    }
    if (var_r4 != 0) {
        return var_r4 + 8;
    }
    return &lbl_804F97B8;
}
