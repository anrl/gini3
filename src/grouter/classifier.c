/*
 * classifier.c (simple packet classifier for gRouter)
 * AUTHOR: Muthucumaru Maheswaran
 * DATE: June 27, 2008

 * This is a simple packet classifier. It is called by the input thread to
 * tag the incoming packet according to the rule set setup by the user.
 * At the start, we have a default queue .. that is, packets are given a default 
 * tag if nothing matches. This collection of routines provide rule management
 * and application of rules to tag each packet. 
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <slack/list.h>
#include "classspec.h"
#include "classifier.h"
#include "ip.h"


// This function creates a rule but does not set the name field.
// It is set when the rule is inserted into the ruletab (rule table).
classrule_t *createClassRule(ip_spec_t *src, ip_spec_t *dst, port_range_t *srcp, 
			     port_range_t *dstp, int prot, int tos)
{
	classrule_t *crule;
	ip_spec_t zero_spec = {{0,0,0,0}, 0};
	port_range_t zero_ports = {0, 0};
	
	if ((crule = (classrule_t *) malloc(sizeof(classrule_t))) == NULL) 
	{
		fatal("[createClassRule]:: Could not allocate memory for class rule structure ");
		return NULL;
	}
	// copy all the parameters into the newly created structure.
	if (src != NULL)
		memcpy(&(crule->srcspec), src, sizeof(ip_spec_t));
	else
		memcpy(&(crule->srcspec), &(zero_spec), sizeof(ip_spec_t));

	if (dst != NULL)
		memcpy(&(crule->dstspec), dst, sizeof(ip_spec_t));
	else
		memcpy(&(crule->srcspec), &(zero_spec), sizeof(ip_spec_t));
	if (srcp != NULL)
		memcpy(&(crule->srcports), srcp, sizeof(port_range_t));
	else
		memcpy(&(crule->srcports), &(zero_ports), sizeof(port_range_t));
	if (dstp != NULL)
		memcpy(&(crule->dstports), dstp, sizeof(port_range_t));
	else
		memcpy(&(crule->dstports), &(zero_ports), sizeof(port_range_t));		
	crule->prot = prot;
	crule->tos = tos;

	// return the structure.
	return crule;
}


// RuleID  RuleTag  SRC IP Src Port  Dst IP Dst Port Prot TOS
void printClassRule(classrule_t *cr)
{
	char tmpbuf[MAX_TMPBUF_LEN];

	printf("%d\t\%s\t", cr->ruleid, cr->ruletag);
	printf("%s/%d\t<%d -- %d>\t", IP2Dot(tmpbuf, cr->srcspec.ip_addr), cr->srcspec.preflen, 
	       cr->srcports.minport, cr->srcports.maxport);
	printf("%s/%d\t<%d -- %d>\t", IP2Dot(tmpbuf, cr->dstspec.ip_addr), cr->dstspec.preflen, 
	       cr->dstports.minport, cr->dstports.maxport);

	printf("%x\t", cr->prot);
	printf("%x\n", cr->tos);
}


void printClassifier(classifier_t *cl)
{
	Lister *lstr;
	classrule_t *ptr;

	printf("\nClassifier name: %s\n", cl->name);
	printf("Number of rules found: %d\n\n", cl->rulecnt);
	printf("\nRule ID\tRule Tag\tSrc IP\t<Src Port Range>\tDst IP\t<Dst Port Range>\tProtocol\tTOS\n");
	lstr = lister_create(cl->ruletab);
	while (ptr = ((classrule_t*)lister_next(lstr)))
		printClassRule(ptr);
	lister_release(lstr);
	printf("\n\n");
}


// create a classifier with the given name 
// if the defrule parameter is 1, initialize with the default rule
classifier_t *createClassifier(char *name, int defrule)
{
	classifier_t *cl;
	classrule_t *crule;

	if ((cl = (classifier_t *) malloc(sizeof(classifier_t))) == NULL)
	{
		fatal("[createClassifier]:: Could not allocate memory for the classifier object..");
		return NULL;
	}

	strcpy(cl->name, name);

	if (!(cl->ruletab = list_create(free)))
	{
		fatal("[createClassifier]:: Could not create the rule list..");
		return NULL;
	}

	cl->rulecnt = 0;
	// the list owns the elements.. memory is managed by the list
	list_own(cl->ruletab, free);

	if (defrule)
	{
		// add default rule..
		crule = createClassRule(NULL, NULL, NULL, NULL, 0, 0);
		addRule(cl, "default", crule);
	}
	return cl;
}



void addRule(classifier_t *classo, char *rname, classrule_t *rule)
{
	strcpy(rule->ruletag, rname);
	rule->ruleid = ++(classo->rulecnt);
	list_prepend(classo->ruletab, rule);
}


void moveDownRule(classifier_t *classo, char *rname)
{
	int i, j, lsize;
	classrule_t *ptr = NULL;

	lsize = list_length(classo->ruletab);
	for(i = 0; i < lsize; i++)
	{
		ptr = list_item(classo->ruletab, i);
		if (strcmp(ptr->ruletag, rname) == 0)
		{
			j = (i+1) % lsize;
			list_remove(classo->ruletab, i);
			break;
		}
	}
	if (ptr != NULL)
		list_insert(classo->ruletab, j, ptr);
}



void moveUpRule(classifier_t *classo, char *rname)
{
	int i, j, lsize;
	classrule_t *ptr = NULL;

	lsize = list_length(classo->ruletab);
	for(i = 0; i < lsize; i++)
	{
		ptr = list_item(classo->ruletab, i);
		if (strcmp(ptr->ruletag, rname) == 0)
		{
			j = (i-1) % lsize;
			list_remove(classo->ruletab, i);
			break;
		}
	}
	if (ptr != NULL)
		list_insert(classo->ruletab, j, ptr);
}




void delRule(classifier_t *classo, char *rname)
{
	classrule_t *ptr;
	Lister *lster;

	for (lster = lister_create(classo->ruletab); lister_has_next(lster) == 1; )
	{
		ptr = (classrule_t *)lister_next(lster);
		if (strcmp(rname, ptr->ruletag) == 0)
		{
			lister_remove(lster);
			break;
		}
	}
	lister_release(lster);
}



// WARNING: The spec should only be defined upto the preflen.
// TODO: Do the matching only up to preflen.. stop at that.
// IMPORTANT:: This routine assumes that all elements (IP and Spec) are in 
// network-byte-order (most significant byte first). 
int compareIP2Spec(uchar ip[], uchar spec[], int preflen)
{
	uchar temp[4] = {0,0,0,0}, mask, tbyte = 0;
	int prefbytes = preflen/8;
	int i, j, rembits;

	for (i = 0; i < prefbytes; i++)
		temp[i] = ip[i];

	if (prefbytes < 4)
	{
		rembits = preflen - (prefbytes * 8);
		mask = 0x80;

		for (j = 0; j < rembits; j++)
		{
			tbyte = tbyte | mask;
			mask = mask >> 1;
		}

		temp[prefbytes] = ip[prefbytes] & tbyte;
	}
	return COMPARE_IP(temp, spec) == 0;
}


int compareProt2Spec(int prot, int pspec)
{
	if (pspec == 0) return 1;
	if (prot == pspec) return 1;
	return 0;
}


int compareTos2Spec(int tos, int tspec)
{
	if (tspec == 0) return 1;
	if (tos == tspec) return 1;
	return 0;
}


// int comparePorts2Spec(int prot, 

// returns 1 if the rule does not match and 0 otherwise
// we check 
int isRuleMatching(classrule_t *crule, gpacket_t *in_pkt)
{
	char tmpbuf[MAX_TMPBUF_LEN];
	ip_packet_t *ip_pkt = (ip_packet_t *)&in_pkt->data.data;

	return compareIP2Spec(ip_pkt->ip_src, gHtonl(tmpbuf, crule->srcspec.ip_addr), crule->srcspec.preflen) *
		compareIP2Spec(ip_pkt->ip_dst, gHtonl(tmpbuf+20, crule->dstspec.ip_addr), crule->dstspec.preflen) *
		compareProt2Spec(ip_pkt->ip_prot, crule->prot) *
		compareTos2Spec(ip_pkt->ip_tos, crule->tos);
}


// returns NULL if nothing matches.. may be we should put the
// packet in the default Queue.
char *tagPacket(classifier_t *classo, gpacket_t *in_pkt)
{
	classrule_t *ptr;
	Lister *lster;
	int found = FALSE;

	verbose(2, "[tagPacket]:: Entering the packet tagging function.. ");

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
		return ptr->ruletag;
	else
		return (char*)NULL;
}



