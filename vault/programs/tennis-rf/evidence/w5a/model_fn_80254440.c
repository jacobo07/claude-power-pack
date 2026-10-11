/* model layer: vtable calls, unk offsets -> struct. PMN: det transform abstained (fn_80259A8C unresolved, unkN on void*) */
typedef struct Obj Obj;
typedef struct VT { char pad[0x10]; void (*f10)(void*); void (*f14)(void*); } VT;
typedef struct Iface { VT *vt; } Iface;
typedef struct Owner { char pad[8]; Iface *i8; Iface *iC; Iface *i10; void *u14; } Owner;
void fn_80259A8C(void*);
void fn_80254440(Owner *o) {
    Iface *a = o->i10;
    a->vt->f14(a);
    fn_80259A8C(o->u14);
    a = o->iC;
    a->vt->f10(a);
    a = o->i8;
    a->vt->f10(a);
}