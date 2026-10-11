/* model layer. PMN: det transform cannot name unkC4/unkC8/unkCC fields or the 0x8 offset return; m2c left '?' return */
typedef struct Node { char pad[8]; int *cur; int *end; } Node;
typedef struct Host { char pad[0xC4]; Node *c4; char *c8; char *cc; } Host;
extern char lbl_804F97B8;
char *fn_80252F34(Host *h) {
    char *r = h->c8;
    if (r == 0) {
        Node *n = h->c4;
        if (n->cur == n->end) r = 0; else r = (char*)*n->cur;
        if (r == 0) {
            r = h->cc;
            if (r == 0) r = 0;
        }
    }
    if (r != 0) return r + 8;
    return &lbl_804F97B8;
}