s32 fn_801CD2D0(s32, s32); /* extern */
void fn_801D022C(s32, s32, s32, s32); /* extern */
extern ? lbl_803D92D0;

void fn_80216640(void *arg0, s32 arg1) {
    fn_801CD2D0(arg0->unk44, &lbl_803D92D0 + 0x56D);
    fn_801D022C(arg1, 0x262, 0, 0);
    fn_801CD2D0(arg0->unk44, &lbl_803D92D0 + 0x579);
    fn_801D022C(arg1, 0x263, 0, 0);
    fn_801CD2D0(arg0->unk44, &lbl_803D92D0 + 0x585);
    fn_801D022C(arg1, 0x264, 0, 0);
    fn_801CD2D0(arg0->unk44, &lbl_803D92D0 + 0x591);
    fn_801D022C(arg1, 0x265, 0, 0);
}
