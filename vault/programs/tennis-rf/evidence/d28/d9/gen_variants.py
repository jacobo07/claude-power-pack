"""WU-D9 deterministic variant generator. Reads the as_is job3s rows (W12), swaps only the function body.
Usage: python gen_variants.py <job3s.jsonl> <out.jsonl>   (<=32 variants per fn; donors copied as-is)"""
import json, sys, re
src, out = sys.argv[1], sys.argv[2]
rows = [json.loads(l) for l in open(src, encoding="utf-8")]
B = {}
B["fn_802128D4"] = [  # dims: cast, comparison form, temporaries, signedness, ternary
 ("cast_eq1_if", "if ((s16) arg0->f_A0->f_06 == 1) { return 1; } return 0;"),
 ("ret_eq", "return (s16) arg0->f_A0->f_06 == 1;"),
 ("ret_eq_nocast", "return arg0->f_A0->f_06 == 1;"),
 ("ret_ternary", "return (arg0->f_A0->f_06 == 1) ? 1 : 0;"),
 ("ret_ne_ternary", "return (arg0->f_A0->f_06 != 1) ? 0 : 1;"),
 ("tmp_ptr", "Sub802128D4 *p = arg0->f_A0; return p->f_06 == 1;"),
 ("tmp_val", "s16 v = arg0->f_A0->f_06; return v == 1;"),
 ("tmp_val_if", "s16 v = arg0->f_A0->f_06; if (v == 1) { return 1; } return 0;"),
 ("tmp_s32", "s32 v = arg0->f_A0->f_06; return v == 1;"),
 ("tmp_u16", "u16 v = arg0->f_A0->f_06; return v == 1;"),
 ("cast_u16", "return (u16) arg0->f_A0->f_06 == 1;"),
 ("cast_s32", "return (s32) arg0->f_A0->f_06 == 1;"),
 ("rev_operands", "return 1 == arg0->f_A0->f_06;"),
 ("rev_operands_cast", "return 1 == (s16) arg0->f_A0->f_06;"),
 ("sub_zero", "return (arg0->f_A0->f_06 - 1) == 0;"),
 ("not_sub", "return !(arg0->f_A0->f_06 - 1);"),
 ("else_form", "if (arg0->f_A0->f_06 == 1) { return 1; } else { return 0; }"),
 ("neg_if", "if (arg0->f_A0->f_06 != 1) { return 0; } return 1;"),
 ("bool_var", "s32 r = 0; if (arg0->f_A0->f_06 == 1) { r = 1; } return r;"),
 ("bool_var_init1", "s32 r = 1; if (arg0->f_A0->f_06 != 1) { r = 0; } return r;"),
 ("tmp_ptr_if", "Sub802128D4 *p = arg0->f_A0; if (p->f_06 == 1) { return 1; } return 0;"),
 ("tmp_ptr_cast", "Sub802128D4 *p = arg0->f_A0; return (s16) p->f_06 == 1;"),
 ("u32_ret", "return (u32) (arg0->f_A0->f_06 == 1);"),
 ("shift_idiom", "return (u32) __cntlzw(arg0->f_A0->f_06 - 1) >> 5;"),
]
B["fn_8032CF78"] = [  # dims: temporaries, cast, pragma-sda declaration
 ("as_is", "arg0->f_04 = lbl_80519F74;"),
 ("tmp_f32", "f32 v = lbl_80519F74; arg0->f_04 = v;"),
 ("tmp_double", "f64 v = lbl_80519F74; arg0->f_04 = (f32) v;"),
 ("cast_f32", "arg0->f_04 = (f32) lbl_80519F74;"),
 ("volatile_free_deref", "f32 *p = &lbl_80519F74; arg0->f_04 = *p;"),
]
PRE = {"fn_8032CF78": [
 ("sda_pragma", "#pragma section sdata \".sdata\" \".sbss\" data_mode=sda_rel\n"),
 ("sda2_pragma", "#pragma section sdata2 \".sdata2\" \".sdata2\" data_mode=sda_rel\n"),
 ("far_decl", "")]}
out_rows = []; log = {}
for fn, vs in B.items():
    for base in [r for r in rows if r["symbol"] == fn and r["variant"] == "as_is"]:
        i = base["source_text"].rindex(fn + "(")  # last occurrence = the definition
        j = base["source_text"].rfind("\n", 0, i) + 1
        head = base["source_text"][:j]
        sig = base["source_text"][j:base["source_text"].index("{", i)]
        n = 0
        for name, body in vs:
            if fn == "fn_8032CF78" and name == "volatile_free_deref":
                pass
            r = dict(base); r["variant"] = "v_" + name
            r["source_text"] = head + sig + "{\n    " + body + "\n}\n"
            r["unit_id"] = "d9-%s-%s-%s" % (fn[3:], base["preset"], name)
            r["producer"] = r["strategy"] = "d9_variant"
            out_rows.append(r); n += 1
        for name, pre in PRE.get(fn, []):
            if name == "far_decl": continue
            r = dict(base); r["variant"] = "v_" + name
            r["source_text"] = head.replace("extern f32 lbl_80519F74;", pre + "extern f32 lbl_80519F74;") + sig + "{\n    arg0->f_04 = lbl_80519F74;\n}\n"
            r["unit_id"] = "d9-%s-%s-%s" % (fn[3:], base["preset"], name)
            r["producer"] = r["strategy"] = "d9_variant"
            out_rows.append(r); n += 1
        log["%s/%s" % (fn, base["preset"])] = n
for d in [r for r in rows if r["producer"] == "w10c_donor"]:
    out_rows.append(d)
assert all(v <= 32 for v in log.values()), log
with open(out, "w", encoding="utf-8", newline="\n") as f:
    for r in out_rows: f.write(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n")
print(json.dumps(log), len(out_rows))
