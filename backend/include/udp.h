#ifndef __UDP_H_
#define __UDP_H_

#include <stdint.h>

typedef struct {
	uint16_t	src_port;		/* source port */
	uint16_t	dst_port;		/* destination port */
	int16_t 	length;         /* udp length */
	uint16_t	checksum;		/* udp checksum */
} udp_packet_type;

typedef struct {
    uint32_t ip_src;
    uint32_t ip_dst;
    uint8_t reserved;
    uint8_t ip_prot;
    int16_t udp_length;
} udp_pseudo_header_type;

uint16_t udp_checksum(ip_packet_t *ip_packet);

#endif // ifndef __UDP_H_
