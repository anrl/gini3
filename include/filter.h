/*
 * filter.h (include file for the packet filter)
 * AUTHOR: Muthucumaru Maheswaran
 * DATE: October 1, 2008
 *
 * These routines implement the packet filter. 
 */

#ifndef __FILTER_H__
#define __FILTER_H__

#include <slack/list.h>
#include "grouter.h"
#include "classspec.h"
#include "message.h"
#include "classifier.h"

// Function prototypes
_begin_decls

void printFilterStats(classifier_t *cl);
void printFilter(classifier_t *cl);
int filteredPacket(classifier_t *classo, gpacket_t *in_pkt);


_end_decls
#endif
