/*
 * filter.c (simple packet filter for gRouter)
 * AUTHOR: Muthucumaru Maheswaran
 * DATE: October 1, 2008

 * This is a simple packet filter. It is called by the input thread to filter
 * an incoming packet according to the rule set configured by the user.
 * At startup, we don't have any filters. have a default queue.

 * NOTE: The routines provided here heavily reuse code provided in
 * classifier.c. Pleae refer to that file to understand how some of the functions
 * are implemented.
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <slack/list.h>
#include "classspec.h"
#include "classifier.h"
#include "ip.h"


void printFilterStats(classifier_t *cl)
{
	

}


void printFilter(classifier_t *cl)
{
	Lister *lstr;
	classrule_t *ptr;

	printf("\nFilter name: %s\n", cl->name);
	printf("Number of rules found: %d\n\n", cl->rulecnt);
	printf("\nRule ID\tRule Tag\tSrc IP\t<Src Port Range>\tDst IP\t<Dst Port Range>\tProtocol\tTOS\n");
	lstr = lister_create(cl->ruletab);
	while (ptr = ((classrule_t*)lister_next(lstr)))
		printClassRule(ptr);
	lister_release(lstr);
	printf("\n\n");
}



// returns 1 if the packet is filtered.. otherwise returns 0
int filteredPacket(classifier_t *classo, gpacket_t *in_pkt)
{
	classrule_t *ptr;
	Lister *lster;
	int found = FALSE;

	verbose(2, "[filteredPacket]:: Entering the packet filtering function.. ");

	for (lster = lister_create(classo->ruletab); lister_has_next(lster) == 1; )
	{
		ptr = (classrule_t*)lister_next(lster);
		if (isRuleMatching(ptr, in_pkt))
		{
			found = TRUE;
			break;
		}
	}
	lister_release(lster);
	if (found)
		return 1;
	else
		return 0;
}
