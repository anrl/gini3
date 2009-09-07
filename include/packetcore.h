/*
 * packetcore.h (include file for the Packet Core)
 * AUTHOR: Muthucumaru Maheswaran
 * DATE: June 30, 2008
 *
 */

#ifndef __PACKET_CORE_H__
#define __PACKET_CORE_H__


#include <slack/std.h>
#include <slack/map.h>
#include <slack/list.h>

#include "message.h"
#include "grouter.h"
#include "simplequeue.h"


typedef struct _pktcore_t
{
	char name[MAX_NAME_LEN];
	pthread_cond_t schwaiting;
	pthread_mutex_t qlock;                // lock for the main queue
	pthread_mutex_t wqlock;               // lock for work queue
	simplequeue_t *outputQ;
	simplequeue_t *workQ;
	Map *queues;
	int lastqid;
	int packetcnt;
	int maxqsize;
	double vclock;
} pktcore_t;


// Function prototypes
_begin_decls
pktcore_t *createPacketCore(char *rname, simplequeue_t *outQ, simplequeue_t *workQ);
void *weightedFairScheduler(void *pc);
simplequeue_t *getCoreQueue(pktcore_t *pcore, char *qname);
void *packetProcessor(void *pc);
int weightedFairQueuer(pktcore_t *pcore, gpacket_t *in_pkt, int pktsize, char *qkey);
int roundRobinQueuer(pktcore_t *pcore, gpacket_t *in_pkt, int pktsize, char *qkey);
void *roundRobinScheduler(void *pc);
_end_decls
#endif
