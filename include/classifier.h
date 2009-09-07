/*
 * classifier.h (include file for the packet classifier)
 * AUTHOR: Muthucumaru Maheswaran
 * DATE: June 27, 2008
 *
 * These routines implement the classifier. It tags a packet based on the classification rules
 * specified within the system. The rules can be added or deleted from the classifier. We
 * start the classifier with a default ("catch all") rule. Therefore, any incoming packet 
 * is guaranteed to be tagged at least using the default tag.
 */

#ifndef __CLASSIFIER_H__
#define __CLASSIFIER_H__

#include <slack/list.h>
#include "grouter.h"
#include "classspec.h"
#include "message.h"

typedef struct _classrule_t
{
	ip_spec_t srcspec;
	ip_spec_t dstspec;
	port_range_t srcports;
	port_range_t dstports;
	int prot;
	int tos;
	char ruletag[MAX_NAME_LEN];
	int ruleid;
} classrule_t;


typedef struct _classifier_t
{
	List *ruletab;
	int rulecnt;
	char name[MAX_NAME_LEN];
} classifier_t;



// Function prototypes
_begin_decls
classifier_t *createClassifier(char *name, int defrule);
classrule_t *createClassRule(ip_spec_t *src, ip_spec_t *dst, port_range_t *srcp, 
			     port_range_t *dstp, int prot, int tos);
void addRule(classifier_t *classo, char *rname, classrule_t *rule);

char *tagPacket(classifier_t *classo, gpacket_t *in_pkt);
_end_decls
#endif
