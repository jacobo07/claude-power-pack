#include "ctx.h"

RectShape::~RectShape()
{
    rf_live = rf_live - 2;
}
