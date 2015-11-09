#ifndef __TCP_H_
#define __TCP_H_

#include <stdint.h>
#include <endian.h>

#include "ip.h"

typedef struct {
	uint16_t src_port;		/* source port */
    uint16_t dst_port;
	uint16_t th_seq;			/* sequence number */
	uint16_t	th_ack;			/* acknowledgement number */
#if __BYTE_ORDER == __LITTLE_ENDIAN
	uint8_t	th_x2:4;		/* (unused) */
	uint8_t	th_off:4;		/* data offset */
#endif
#if __BYTE_ORDER == __BIG_ENDIAN
	uint8_t	th_off:4;		/* data offset */
	uint8_t	th_x2:4;		/* (unused) */
#endif
	uint8_t	th_flags;
#define	TH_FIN	0x01
#define	TH_SYN	0x02
#define	TH_RST	0x04
#define	TH_PUSH	0x08
#define	TH_ACK	0x10
#define	TH_URG	0x20
	uint16_t	th_win;			/* window */
	uint16_t	th_sum;			/* checksum */
	uint16_t	th_urp;			/* urgent pointer */
} tcp_packet_type;

uint16_t tcp_checksum(ip_packet_t *ip_packet);

#endif // ifndef __TCP_H_
