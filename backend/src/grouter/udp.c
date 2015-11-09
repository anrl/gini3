#include "grouter.h"
#include "ip.h"

#include "udp.h"

uint16_t udp_checksum(ip_packet_t *ip_packet)
{
    udp_packet_type *udp_packet = (udp_packet_type *)
        (ip_packet + (ip_packet->ip_hdr_len * 4));

    udp_pseudo_header_type pseudo_header;
    COPY_IP(&pseudo_header.ip_src, ip_packet->ip_src);
    COPY_IP(&pseudo_header.ip_dst, ip_packet->ip_dst);
    pseudo_header.reserved = 0;
    pseudo_header.ip_prot = ip_packet->ip_prot;
    pseudo_header.udp_length = udp_packet->length;

    uint16_t buf[3];
    buf[0] = ~checksum((uint8_t *) &pseudo_header, sizeof(udp_pseudo_header_type) / 2);
    buf[1] = ~checksum((uint8_t *) &udp_packet, udp_packet->length / 2);
    if (udp_packet->length % 2 != 0)
    {
        uint8_t *temp = (uint8_t *) (udp_packet + udp_packet->length - 1);
        buf[2] = *temp << 8;
    }
    else
    {
        buf[2] = 0;
    }

    return checksum((uint8_t *) &buf, 3);
}
