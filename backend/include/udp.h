#ifndef __UDP_H_
#define __UDP_H_

#include <stdint.h>

typedef struct
{
    uint16_t src_port;
    uint16_t dst_port;
} udp_packet_type;

#endif // ifndef __UDP_H_
