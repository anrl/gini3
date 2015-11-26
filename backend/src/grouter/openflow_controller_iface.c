#include <pthread.h>

#include "message.h"

#include "openflow_controller_iface.h"

void *openflow_controller_iface(void *pn) {
    int *port_num = (int *)pn;
    if (*port_num < 1 || *port_num > 65535) {
        fatal("[openflow_controller_iface]:: Invalid port number"
            " %d", *port_num);
        exit(1);
    }

    verbose(1, "[openflow_controller_iface]:: Connecting to controller.");
	// pktcore_t *pcore = (pktcore_t *)pc;
	// gpacket_t *in_pkt;
	// int pktsize;
    //
	// pthread_setcanceltype(PTHREAD_CANCEL_ASYNCHRONOUS, NULL);
	// while (1)
	// {
	// 	verbose(2, "[openflowPacketProcessor]:: Waiting for a packet...");
	// 	readQueue(pcore->openflowWorkQ, (void **)&in_pkt, &pktsize);
	// 	pthread_testcancel();
	// 	verbose(2, "[openflowPacketProcessor]:: Got a packet for further"
	// 		" processing..");
    //
	// 	openflow_flowtable_handle_packet(in_pkt, pcore);
	// }
    free(pn);
}

pthread_t openflow_controller_iface_init(int port_num) {
	int threadstat;
	pthread_t threadid;

    int *pn = malloc(sizeof(int));
    *pn = port_num;
	threadstat = pthread_create((pthread_t *)&threadid, NULL,
		(void *)openflow_controller_iface, pn);
	return threadid;
}



void openflow_send_packet_to_controller(gpacket_t *packet)
{
	// TODO: Implement this function
}

void openflow_parse_packet_from_controller(gpacket_t *packet)
{
	// TODO: Implement this function
}
