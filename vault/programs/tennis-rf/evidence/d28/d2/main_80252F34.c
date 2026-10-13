u8 *fn_80252F34(Obj80252F34 *arg0) {
    Item80252F34 **temp_r5;
    Item80252F34 *var_r4;
    Vec80252F34 *temp_r4;

    var_r4 = arg0->f_C8;
    if (var_r4 != NULL) {

    } else {
        temp_r4 = arg0->f_C4;
        temp_r5 = temp_r4->f_08;
        if (temp_r5 == (Item80252F34 **) temp_r4->f_0C) {
            var_r4 = NULL;
        } else {
            var_r4 = *temp_r5;
        }
        if (var_r4 != NULL) {

        } else {
            var_r4 = arg0->f_CC;
            if (var_r4 != NULL) {

            } else {
                var_r4 = NULL;
            }
        }
    }
    if (var_r4 != NULL) {
        return var_r4->f_08;
    }
    return lbl_804F97B8;
}
