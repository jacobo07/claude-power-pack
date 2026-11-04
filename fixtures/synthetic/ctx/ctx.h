/* Synthetic corpus context -- original code written for the public Reconstruction Factory. Not derived from any binary. */
#ifndef RF_CTX_H
#define RF_CTX_H

typedef signed char s8;
typedef unsigned char u8;
typedef short s16;
typedef unsigned short u16;
typedef int s32;
typedef unsigned int u32;
typedef float f32;

typedef struct RfVec2 {
    s32 x;
    s32 y;
} RfVec2;

typedef struct RfRect {
    s32 x;
    s32 y;
    s32 w;
    s32 h;
} RfRect;

typedef struct RfNode {
    s32 value;
    struct RfNode *next;
} RfNode;

#ifdef __cplusplus
extern "C" {
#endif
extern s32 rf_ring[16];
extern s32 rf_ring_head;
extern s32 rf_counter;
extern s32 rf_live;
extern s32 rf_sink;
extern const f32 rf_flt_half;
#ifdef __cplusplus
}

struct Shape {
    s32 id;
    Shape(s32 i);
    virtual s32 area() const;
    virtual s32 scale(s32 k);
    virtual ~Shape();
};

struct RectShape : Shape {
    s32 w;
    s32 h;
    RectShape(s32 i, s32 ww, s32 hh);
    s32 area() const;
    virtual ~RectShape();
};

struct CircleShape : Shape {
    s32 r;
    CircleShape(s32 i, s32 rr);
    s32 area() const;
    s32 scale(s32 k);
};

struct Counter {
    s32 n;
    void inc();
    s32 get() const;
    void add(s32 d);
    void reset();
    ~Counter();
};
#endif

#endif
