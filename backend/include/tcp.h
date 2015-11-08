#ifndef __TCP_H_
#define __TCP_H_

#include <stdint.h>

typedef struct
{
    uint16_t src_port;
    uint16_t dst_port;
} tcp_packet_type;

#endif // ifndef __TCP_H_
