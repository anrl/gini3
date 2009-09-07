/*
 * packetcore.c (This is the core of the gRouter)
 * AUTHOR: Muthucumaru Maheswaran
 * DATE: June 30, 2008

 * The functions provided by this collection mimics the input queues
 * and the interconnection network in a typical router. In this software
 * implementation, we provide a collection of input queues into which the
 * packet classifier inserts the packets. For now, the packets have a
 * drop on full policy. The packet scheduler is responsible for picking a
 * packet from the collection of active input queues. The packet scheduler
 * inserts the chosen packet into a work queue that is not part of the 
 * packet core. The work queue is serviced by one or more worker threads 
 * (for now we have one worker thread). 
 */
#define _XOPEN_SOURCE             500
#include <unistd.h>
#include <slack/std.h>
#include <slack/map.h>
#include <slack/list.h>
#include <pthread.h>
#include "protocols.h"
#include "packetcore.h"
#include "message.h"
#include "grouter.h"


pktcore_t *createPacketCore(char *rname, simplequeue_t *outQ, simplequeue_t *workQ)
{
	pktcore_t *pcore;

	if ((pcore = (pktcore_t *) malloc(sizeof(pktcore_t))) == NULL)
	{
		fatal("[createPktCore]:: Could not allocate memory for packet core structure");
		return NULL;
	}
	
	strcpy(pcore->name, rname);
	pthread_mutex_init(&(pcore->qlock), NULL);
	pthread_mutex_init(&(pcore->wqlock), NULL);
	pthread_cond_init(&(pcore->schwaiting), NULL);
	pcore->lastqid = 0;
	pcore->packetcnt = 0;
	pcore->outputQ = outQ;
	pcore->workQ = workQ;
	pcore->maxqsize = MAX_QUEUE_SIZE;

	if (!(pcore->queues = map_create(NULL)))
	{
		fatal("[createPacketCore]:: Could not create the queues..");
		return NULL;
	}

	verbose(6, "[createPacketCore]:: packet core successfully created ...");
	return pcore;
}


int addPktCoreQueue(pktcore_t *pcore, char *qname, char *qtag, double qweight)
{
	simplequeue_t *pktq;


	if ((pktq = createSimpleQueue(qname, pcore->maxqsize, 0, 0)) == NULL)
	{
		error("[addPktCoreQueue]:: packet queue creation failed.. ");
		return EXIT_FAILURE;
	}

	pktq->weight = qweight;
	pktq->stime = pktq->ftime = 0.0;
	
	map_add(pcore->queues, qtag, pktq);
	return EXIT_SUCCESS;
}


simplequeue_t *getCoreQueue(pktcore_t *pcore, char *qname)
{
	return map_get(pcore->queues, qname);
}


int delPktCoreQueue(pktcore_t *pcore, char *qname)
{
	// NOT YET IMPLEMENTED
	return EXIT_SUCCESS;
}



// create a thread for the scheduler. for now, hook up the Worst-case WFQ
// as the scheduler. Only the dequeue is hooked up. The enqueue part is 
// in the classifier. The dequeue will put the scheduler in wait when it
// runs out of jobs in the queue. The enqueue will wake up a sleeping scheduler.
int PktCoreSchedulerInit(pktcore_t *pcore)
{
	int threadstat, threadid;

	threadstat = pthread_create((pthread_t *)&threadid, NULL, (void *)roundRobinScheduler, (void *)pcore);
	if (threadstat != 0)
	{
		verbose(1, "[PKTCoreSchedulerInit]:: unable to create thread.. ");
		return -1;
	}

	return threadid;
}


int PktCoreWorkerInit(pktcore_t *pcore)
{
	int threadstat, threadid;

	threadstat = pthread_create((pthread_t *)&threadid, NULL, (void *)packetProcessor, (void *)pcore);
	if (threadstat != 0)
	{
		verbose(1, "[PKTCoreWorkerInit]:: unable to create thread.. ");
		return -1;
	}

	return threadid;
}


void *packetProcessor(void *pc)
{
	pktcore_t *pcore = (pktcore_t *)pc;
	gpacket_t *in_pkt;
	int pktsize;

	pthread_setcanceltype(PTHREAD_CANCEL_ASYNCHRONOUS, NULL);
	while (1)
	{
		verbose(2, "[packetProcessor]:: Waiting for a packet...");
		readQueue(pcore->workQ, (void **)&in_pkt, &pktsize);
		pthread_testcancel();
		verbose(2, "[packetProcessor]:: Got a packet for further processing..");		

		// get the protocol field within the packet... and switch it accordingly
		switch (ntohs(in_pkt->data.header.prot))
		{
		case IP_PROTOCOL:
			verbose(2, "[packetProcessor]:: Packet sent to IP routine for further processing.. ");
			
			IPIncomingPacket(in_pkt);
			break;
		case ARP_PROTOCOL:
			verbose(2, "[packetProcessor]:: Packet sent to ARP module for further processing.. ");
			ARPProcess(in_pkt);
			break;
		default:
			verbose(1, "[packetProcessor]:: Packet discarded: Unknown protocol protocol");
			// TODO: should we generate ICMP errors here.. check router RFCs
			break;
		}
	}
}



