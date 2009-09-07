/*
 * classspec.h (include file for the classifier specifications)
 * AUTHOR: Muthucumaru Maheswaran
 * DATE: June 27, 2008
 *
 * The classifier specifications are used by the classifier to define
 * basic elements such as IP address specifiers and port range specifiers in
 * the matching rules. A matching rule for a queue can include a 5-tuple
 * specifier.
 */

#ifndef __CLASS_SPEC_H__
#define __CLASS_SPEC_H__

#include "grouter.h"


typedef struct _ip_spec_t
{
	uchar ip_addr[4];
	int preflen;
} ip_spec_t;


typedef struct _port_range_t
{
	int minport;
	int maxport;
} port_range_t;


// Function prototypes
_begin_decls

_end_decls
#endif
