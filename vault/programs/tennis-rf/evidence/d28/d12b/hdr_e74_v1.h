/* D12b arm-2 layout fact, global lbl_80513E74 (pack-half evidence only). Fields cite the load displacement. */
typedef struct E74Vt { u8 pad_00[0x90]; void *f_90; /* +0x90 */ u8 pad_94[0x18]; void *f_AC; /* +0xAC */ void *f_B0; /* +0xB0 */ void *f_B4; /* +0xB4 */ } E74Vt;
typedef struct E74W { u8 pad_00[0x9C]; void *f_9C; /* +0x9C */ } E74W;
typedef struct E74Obj { E74Vt *f_00; /* +0x0 */ u8 pad_04[0xFC]; void *f_100; /* +0x100 */ u8 pad_104[0x5A0]; void *f_6A8; /* +0x6A8 */ u8 pad_6AC[0x354]; E74W *f_A00; /* +0xA00 */ u8 pad_A04[0x48]; u8 f_A4C; /* +0xA4C */ } E74Obj;
extern E74Obj *lbl_80513E74;