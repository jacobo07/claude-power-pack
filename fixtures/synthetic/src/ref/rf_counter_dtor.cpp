#include "ctx.h"

Counter::~Counter()
{
    rf_live = rf_live - 1;
}
