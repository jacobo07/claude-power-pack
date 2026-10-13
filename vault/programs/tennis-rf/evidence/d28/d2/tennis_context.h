/* tennis_context.h -- m2c --context type context for the Tennis W5a draw (12 functions, MEASURE.md W5a; WU-W11).
 * Source: the DTK disassembly of SportsPackEP.dol (wst_tennis/step0/split_sports/out/asm), read with
 * trf/evidence/w11/dumpasm.py. Every named struct member cites the load/store displacement it comes from as
 * `+0xNN` (test_tennis_context.py checks the cited offset against m2c's own layout of the member). Names are
 * offset-derived (f_XX / m_XX): the asm gives layout, not names. Pads place each member at exactly its offset.
 * Prototypes cite the argument registers the asm reads and the value it leaves in r3. Nothing here is m2c output.
 * Pure C declarations, valid as C and C++. The prelude is the Dolphin SDK base types (dolphin/types.h), ported
 * from CP50 arm_a.M2C_TYPES: a unit built from this header carries it once, never twice. */
typedef signed char s8;
typedef signed short s16;
typedef signed long s32;
typedef signed long long s64;
typedef unsigned char u8;
typedef unsigned short u16;
typedef unsigned long u32;
typedef unsigned long long u64;
typedef float f32;
typedef double f64;

/* ---- fn_8022F90C: `add r3,r3,r4; lbz r3,0x2a(r3)` -- byte at +0x2A of the object at arg0 + arg1 (arg1 unscaled:
 *      no slwi/mulli before the add, so a byte offset or a byte-array index) ---- */
typedef struct Obj8022F90C {
    u8 pad_00[0x2A];
    u8 f_2A; /* +0x2A lbz r3,0x2a(r3) */
} Obj8022F90C;
u8 fn_8022F90C(Obj8022F90C *arg0, s32 arg1);

/* ---- fn_80203FEC: `slwi r0,r4,3; lbzx r3,r3,r0` -- first byte of an 8-byte element arg0[arg1] ---- */
typedef struct Elem80203FEC {
    u8 f_00;        /* +0x00 lbzx r3,r3,r0 (r0 = r4 << 3) */
    u8 pad_01[7];   /* element stride 8 = slwi r0,r4,3 */
} Elem80203FEC;
u8 fn_80203FEC(Elem80203FEC *arg0, s32 arg1);

/* ---- fn_8020711C: `lwz r3,0x1c(r3); subi r0,r3,2; cntlzw; srwi 5` = (f_1C == 2) ---- */
typedef struct Obj8020711C {
    u8 pad_00[0x1C];
    s32 f_1C; /* +0x1C lwz r3,0x1c(r3) */
} Obj8020711C;
s32 fn_8020711C(Obj8020711C *arg0);

/* ---- fn_8021EAA8: `slwi r4,r4,4; slwi r0,r5,2; add; add; lwz r3,0x14(r3)` -- rows of 0x10 bytes, s32 cells ---- */
typedef struct Row8021EAA8 {
    s32 f_00[4]; /* +0x00 cell stride 4 = slwi r0,r5,2; row stride 0x10 = slwi r4,r4,4 */
} Row8021EAA8;
typedef struct Obj8021EAA8 {
    u8 pad_00[0x14];
    Row8021EAA8 f_14[1]; /* +0x14 lwz r3,0x14(r3) after the row/cell adds */
} Obj8021EAA8;
s32 fn_8021EAA8(Obj8021EAA8 *arg0, s32 arg1, s32 arg2);

/* ---- fn_8020CC14: `lwz r0,0x0(r3)`, `lwz r0,0x8(r3)`, `lbz r0,0x10(r3)`; r4 compared with cmpw ---- */
typedef struct Obj8020CC14 {
    s32 f_00;      /* +0x00 lwz r0,0x0(r3) */
    u8 pad_04[4];
    s32 f_08;      /* +0x08 lwz r0,0x8(r3) */
    u8 pad_0C[4];
    u8 f_10;       /* +0x10 lbz r0,0x10(r3) */
} Obj8020CC14;
s32 fn_8020CC14(Obj8020CC14 *arg0, s32 arg1);

/* ---- fn_80241018: `lwz r0,0x0/0x4/0x8(r3)`, each `cmpwi r0,0x3` ---- */
typedef struct Obj80241018 {
    s32 f_00; /* +0x00 lwz r0,0x0(r3) */
    s32 f_04; /* +0x04 lwz r0,0x4(r3) */
    s32 f_08; /* +0x08 lwz r0,0x8(r3) */
} Obj80241018;
s32 fn_80241018(Obj80241018 *arg0);

/* ---- fn_801BD194: r3 passed through, `li r4,0x8; li r5,0x0; b fn_801BD1A0` (tail call) ----
 * fn_801BD1A0 saves r3/r4/r5 (`mr r28,r3; mr r29,r4; mr r27,r5`), stores `stw r30,0x8(r28)` (r3 is a pointer)
 * and returns `mr r3,r31` (r31 starts `li r31,0x0`): s32 (void *, s32, s32). */
s32 fn_801BD1A0(void *arg0, s32 arg1, s32 arg2);
s32 fn_801BD194(void *arg0);

/* ---- shared callees of fn_80257978 / fn_8025C600 / fn_8022621C ----
 * fn_800B4548: reads only r3 (`mr r28,r3`, then `bl fn_801063E0`); callers ignore r3 after it.
 * fn_800BC298, fn_801F331C: read r3 and r4 (`cmpwi r3,0x0`, `cmpwi r4,0x0` / `mr r31,r4`), return r3 unchanged
 * (`mr r31,r3 ... mr r3,r31` / `mr r30,r3 ... mr r3,r30`). */
void fn_800B4548(s32 arg0);
s32 fn_800BC298(s32 arg0, s32 arg1);
s32 fn_801F331C(s32 arg0, s32 arg1);

/* ---- fn_80257978: `cmpwi r3,0; cmpwi r4,0; ble; bl fn_800B4548` with r3 = arg0; returns `mr r3,r31` = arg0 ---- */
s32 fn_80257978(s32 arg0, s32 arg1);

/* ---- fn_8025C600: `li r4,0x0; bl fn_801F331C` (r3 = arg0), then `mr r3,r30; bl fn_800B4548`; returns arg0 ---- */
s32 fn_8025C600(s32 arg0, s32 arg1);

/* ---- fn_8022621C: `li r4,0x0; bl fn_800BC298` (r3 = arg0), then `mr r3,r30; bl fn_800B4548`; returns arg0 ---- */
s32 fn_8022621C(s32 arg0, s32 arg1);

/* ---- fn_80254440: `mr r31,r3`; three virtual calls `lwz r3,N(r31); lwz r12,0x0(r3); lwz r12,M(r12); bctrl`
 *      with this = the loaded r3, and `lwz r3,0x14(r31); bl fn_80259A8C` ---- */
struct Sub80254440;
typedef struct Vt80254440 {
    u8 pad_00[0x10];
    void (*m_10)(struct Sub80254440 *); /* +0x10 lwz r12,0x10(r12) (via f_08 and f_0C) */
    void (*m_14)(struct Sub80254440 *); /* +0x14 lwz r12,0x14(r12) (via f_10) */
} Vt80254440;
typedef struct Sub80254440 {
    Vt80254440 *vt; /* +0x00 lwz r12,0x0(r3) */
} Sub80254440;
typedef struct Obj80254440 {
    u8 pad_00[0x8];
    Sub80254440 *f_08; /* +0x08 lwz r3,0x8(r31) */
    Sub80254440 *f_0C; /* +0x0C lwz r3,0xc(r31) */
    Sub80254440 *f_10; /* +0x10 lwz r3,0x10(r3) */
    void *f_14;        /* +0x14 lwz r3,0x14(r31) -> fn_80259A8C */
} Obj80254440;
/* fn_80259A8C: `mr r31,r3`, then `lwz r0,0x8(r3)`, `stfs f2,0x68(r3)`: one pointer argument; r3 unused by caller */
void fn_80259A8C(void *arg0);
void fn_80254440(Obj80254440 *arg0);

/* ---- fn_80252F34: `lwz r4,0xc8(r3)`; else `lwz r4,0xc4(r3); lwz r5,0x8(r4); lwz r0,0xc(r4); cmplw r5,r0`
 *      (begin == end -> 0, else `lwz r4,0x0(r5)`); else `lwz r4,0xcc(r3)`; result `addi r3,r4,0x8`, or
 *      `lis/addi lbl_804F97B8` when all three are 0 ---- */
typedef struct Item80252F34 {
    u8 pad_00[0x8];
    u8 f_08[1]; /* +0x08 addi r3,r4,0x8 (address returned) */
} Item80252F34;
typedef struct Vec80252F34 {
    u8 pad_00[0x8];
    Item80252F34 **f_08; /* +0x08 lwz r5,0x8(r4) (begin; `lwz r4,0x0(r5)` = first element) */
    Item80252F34 **f_0C; /* +0x0C lwz r0,0xc(r4) (end; cmplw r5,r0) */
} Vec80252F34;
typedef struct Obj80252F34 {
    u8 pad_00[0xC4];
    Vec80252F34 *f_C4;  /* +0xC4 lwz r4,0xc4(r3) */
    Item80252F34 *f_C8; /* +0xC8 lwz r4,0xc8(r3) */
    Item80252F34 *f_CC; /* +0xCC lwz r4,0xcc(r3) */
} Obj80252F34;
extern u8 lbl_804F97B8[];
u8 *fn_80252F34(Obj80252F34 *arg0);

/* ======== W12 draw (MEASURE.md "W12 draw", trf/evidence/w12/draw.json): 12 new functions, same citation rule ======== */

/* ---- fn_80203E40: `li r0,0x0; stw r0,0x44(r3)` ---- */
typedef struct Obj80203E40 {
    u8 pad_00[0x44];
    s32 f_44; /* +0x44 stw r0,0x44(r3) */
} Obj80203E40;
void fn_80203E40(Obj80203E40 *arg0);

/* ---- fn_8032CF78: `lfs f0,lbl_80519F74@sda21; stfs f0,0x4(r3)` ---- */
typedef struct Obj8032CF78 {
    u8 pad_00[0x4];
    f32 f_04; /* +0x04 stfs f0,0x4(r3) */
} Obj8032CF78;
extern f32 lbl_80519F74;
void fn_8032CF78(Obj8032CF78 *arg0);

/* ---- fn_80230ABC: `lwz r3,0x4(r3); slwi r0,r4,3; add r3,r3,r0` -- address of the 8-byte element f_04[arg1] ---- */
typedef struct Elem80230ABC {
    u8 pad_00[8]; /* element stride 8 = slwi r0,r4,3 (contents not read here) */
} Elem80230ABC;
typedef struct Obj80230ABC {
    u8 pad_00[0x4];
    Elem80230ABC *f_04; /* +0x04 lwz r3,0x4(r3) */
} Obj80230ABC;
Elem80230ABC *fn_80230ABC(Obj80230ABC *arg0, s32 arg1);

/* ---- fn_8027A154: `slwi r0,r4,2; add r3,r3,r0; lwz r3,0x8(r3); stw r5,0x48(r3)` ---- */
typedef struct Sub8027A154 {
    u8 pad_00[0x48];
    s32 f_48; /* +0x48 stw r5,0x48(r3) */
} Sub8027A154;
typedef struct Obj8027A154 {
    u8 pad_00[0x8];
    Sub8027A154 *f_08[1]; /* +0x08 lwz r3,0x8(r3) after `add r3,r3,(r4 << 2)` (pointer stride 4) */
} Obj8027A154;
void fn_8027A154(Obj8027A154 *arg0, s32 arg1, s32 arg2);

/* ---- fn_802128D4: `lwz r3,0xa0(r3); lha r0,0x6(r3); cmpwi r0,0x1` -> 1 / 0 ---- */
typedef struct Sub802128D4 {
    u8 pad_00[0x6];
    s16 f_06; /* +0x06 lha r0,0x6(r3) */
} Sub802128D4;
typedef struct Obj802128D4 {
    u8 pad_00[0xA0];
    Sub802128D4 *f_A0; /* +0xA0 lwz r3,0xa0(r3) */
} Obj802128D4;
s32 fn_802128D4(Obj802128D4 *arg0);

/* ---- fn_8021F8BC: loop i = 0..1 over `lwz r3,0x44(r31)` (r31 = arg0 + 4*i, `addi r31,r31,0x4; cmpwi r30,0x2`),
 *      `bl fn_801CD3A0`, then `lwz r3,0x20(r28); mr r5,r29; bl fn_801CCBB4`; returns i or -1 ----
 * fn_801CD3A0: `cmpwi r3,0x0`, virtual call `lwz r12,0xc(r12)` on r3, returns `mr r3,r0` = arg0 or 0: void *(void *).
 * fn_801CCBB4: `lhz r0,0x0(r3)`, `lwz r4,0x1c(r3)`, r4 -> `mr r6,r4` -> r3 of fn_801D04CC, r5 passed on; returns
 *      `mr r3,r4` (0 or the callee's r3): s32 (void *, void *, s32). */
void *fn_801CD3A0(void *arg0);
s32 fn_801CCBB4(void *arg0, void *arg1, s32 arg2);
typedef struct Obj8021F8BC {
    u8 pad_00[0x20];
    void *f_20;    /* +0x20 lwz r3,0x20(r28) */
    u8 pad_24[0x20];
    void *f_44[2]; /* +0x44 lwz r3,0x44(r31), stride 4 = addi r31,r31,0x4, count 2 = cmpwi r30,0x2 */
} Obj8021F8BC;
s32 fn_8021F8BC(Obj8021F8BC *arg0, s32 arg1);

/* ---- fn_80230BF8: `lwz r3,0x4(r3); bl fn_8022EBF8; lwz r3,0x4(r31); bl fn_8022EBF0` ----
 * fn_8022EBF8 / fn_8022EBF0: `lwz r3,lbl_80513D50@sda21` / `lwz r3,lbl_80513D38@sda21`, then a tail call: the
 *      caller's r3 is passed (`lwz r3,0x4(r31)`) and discarded; no result is read after the call. */
void fn_8022EBF8(void *arg0);
void fn_8022EBF0(void *arg0);
typedef struct Obj80230BF8 {
    u8 pad_00[0x4];
    void *f_04; /* +0x04 lwz r3,0x4(r3) / lwz r3,0x4(r31) */
} Obj80230BF8;
void fn_80230BF8(Obj80230BF8 *arg0);

/* ---- fn_80279E44: `mr r31,r3; bl fn_802773E4` (r3 = arg0), `stw r3,0x0(r31)` = &lbl_80419D20 (vtable,
 *      .obj in the data section), `stw r0,0x28(r31)` = 0; returns `mr r3,r31` = arg0 ----
 * fn_802773E4: `mr r31,r3; bl fn_801F3374; ... stw r4,0x0(r31)`, returns `mr r3,r31` = arg0: void *(void *). */
void *fn_802773E4(void *arg0);
extern void *lbl_80419D20[];
typedef struct Obj80279E44 {
    void **f_00;  /* +0x00 stw r3,0x0(r31) (vtable pointer) */
    u8 pad_04[0x24];
    s32 f_28;     /* +0x28 stw r0,0x28(r31) */
} Obj80279E44;
Obj80279E44 *fn_80279E44(Obj80279E44 *arg0);

/* ---- fn_8021F3E4: MWCC pointer-to-member call. `lwz r0,0x0(r3); lwz r3,0x1c(r3); mulli r0,r0,0xc; add` ->
 *      element f_1C[f_00] (stride 0xC) to fn_800C2890; then `lwz r3,0x14(r31)`, `add r12,r4,r0`, bl fn_800C28C0 ----
 * fn_800C2890: `lwz r5/r6/r7,0x0/0x4/0x8(r3)`, returns 1 if any is nonzero else 0 (ptmf test): s32 (Ptmf *).
 * fn_800C28C0: reads r3 (this, `add r3,r3,r0`) and r12 (the ptmf, `lwz r0,0x0(r12)`...), then `bctr` with r4
 *      untouched; the caller's r4 is `lwz r4,0x1c(r31)`. m2c models r3/r4 only (r12 is not an argument register). */
typedef struct Ptmf8021F3E4 {
    s32 f_00; /* +0x00 lwz r0,0x0(r12) / lwz r5,0x0(r3) in fn_800C2890 (this delta) */
    s32 f_04; /* +0x04 lwz r11,0x4(r12) / lwz r6,0x4(r3) (vtable offset, <0 = non-virtual) */
    s32 f_08; /* +0x08 lwz r12,0x8(r12) / lwz r7,0x8(r3) (function or vtable slot) */
} Ptmf8021F3E4;
s32 fn_800C2890(Ptmf8021F3E4 *arg0);
void fn_800C28C0(void *arg0, Ptmf8021F3E4 *arg1);
typedef struct Obj8021F3E4 {
    s32 f_00;            /* +0x00 lwz r0,0x0(r3) (index, `mulli r0,r0,0xc`) */
    u8 pad_04[0x10];
    void *f_14;          /* +0x14 lwz r3,0x14(r31) */
    u8 pad_18[0x4];
    Ptmf8021F3E4 *f_1C;  /* +0x1C lwz r3,0x1c(r3) / lwz r4,0x1c(r31) */
} Obj8021F3E4;
void fn_8021F3E4(Obj8021F3E4 *arg0);

/* ---- fn_80253348: arg0 in r30, arg1 in r31; global `lwz r5,lbl_80513F98@sda21` ----
 *      r3 = arg1->f_1E0, r4 = arg1, r5 = !(G->f_24->f_1A0->f_18[arg0->f_40] & 1) -> fn_8025043C;
 *      arg0->f_0C->vt->m_3C(arg0->f_0C, arg1); then for k = 1, 3: G->f_18->f_04[arg0->f_40 ^ k]->f_0C->vt->m_38(.., arg1)
 * fn_8025043C: `mr r24,r3; mr r25,r4; mr r26,r5` (three args); the caller reads no result: void. */
struct Sub80253348;
typedef struct Vt80253348 {
    u8 pad_00[0x38];
    void (*m_38)(struct Sub80253348 *, void *); /* +0x38 lwz r12,0x38(r12) */
    void (*m_3C)(struct Sub80253348 *, void *); /* +0x3C lwz r12,0x3c(r12) */
} Vt80253348;
typedef struct Sub80253348 {
    Vt80253348 *vt; /* +0x00 lwz r12,0x0(r3) */
} Sub80253348;
typedef struct Flags80253348 {
    u8 pad_00[0x18];
    s32 f_18[4]; /* +0x18 lwz r0,0x18(r5) after `add r5,r5,(f_40 << 2)`; `clrlwi r0,r0,31` */
} Flags80253348;
typedef struct Mid80253348 {
    u8 pad_00[0x1A0];
    Flags80253348 *f_1A0; /* +0x1A0 lwz r5,0x1a0(r5) */
} Mid80253348;
typedef struct Slot80253348 {
    u8 pad_00[0xC];
    Sub80253348 *f_0C; /* +0x0C lwz r3,0xc(r3) */
} Slot80253348;
typedef struct Tab80253348 {
    u8 pad_00[0x4];
    Slot80253348 *f_04[4]; /* +0x04 lwz r3,0x4(r3) after `add r3,r3,((f_40 ^ k) << 2)` */
} Tab80253348;
typedef struct Glob80253348 {
    u8 pad_00[0x18];
    Tab80253348 *f_18;  /* +0x18 lwz r3,0x18(r3) */
    u8 pad_1C[0x8];
    Mid80253348 *f_24;  /* +0x24 lwz r5,0x24(r5) */
} Glob80253348;
typedef struct Arg80253348 {
    u8 pad_00[0x1E0];
    void *f_1E0; /* +0x1E0 lwz r3,0x1e0(r4) */
} Arg80253348;
typedef struct Obj80253348 {
    u8 pad_00[0xC];
    Sub80253348 *f_0C; /* +0x0C lwz r3,0xc(r30) */
    u8 pad_10[0x30];
    s32 f_40;          /* +0x40 lwz r0,0x40(r3) / lwz r0,0x40(r30) */
} Obj80253348;
extern Glob80253348 *lbl_80513F98;
void fn_8025043C(void *arg0, Arg80253348 *arg1, s32 arg2);
void fn_80253348(Obj80253348 *arg0, Arg80253348 *arg1);

/* ---- fn_80278FEC / fn_803315A0: same shape as fn_80257978 (`cmpwi r3,0x0`, `cmpwi r4,0x0`/`cmpwi r31,0x0` +
 *      `ble`, `bl fn_800B4548` / `li r4,0x0; bl fn_801F331C`), return `mr r3,r30` / `mr r3,r31` = arg0 ---- */
s32 fn_80278FEC(s32 arg0, s32 arg1);
s32 fn_803315A0(s32 arg0, s32 arg1);
