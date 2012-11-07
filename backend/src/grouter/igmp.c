#include "protocols.h"
#include "igmp.h"
#include "ip.h"
#include "message.h"
#include "grouter.h"
#include <slack/err.h>
#include <netinet/in.h>
#include <sys/time.h>
#include <stdio.h>
#include <string.h>

int GetByteOrder() {
  union {
    short s;
    char c[sizeof(short)];
  }un;

  un.s = 0x0102;

  if (un.c[0] == 1 && un.c[1] == 2) {
    return BIGENDIAN;
  }
  else if (un.c[0] == 2 && un.c[1] == 1) {
    return LITTLEENDIAN;
  }
}

int SwitchNibbleBytes(int nibble) {
  int output_nibble = 0;
  output_nibble |= (nibble & 8) >> 3; 
  output_nibble |= (nibble & 4) >> 1; 
  output_nibble |= (nibble & 2) << 1; 
  output_nibble |= (nibble & 1) << 3; 
  return output_nibble;
}

int IGMPProcess(gpacket_t *in_pkt) {
  ip_packet_t *ip_packet = (ip_packet_t *)in_pkt->data.data;
	int ip_header_length = ip_pkt->ip_hdr_len *4;
 
  igmp_header_t igmp_header (igmp_header_t)malloc(IGMP_HEADER_SIZE);
  memcpy(igmp_header, (char* ip_packet) + ip_header_length, IGMP_HEADER_SIZE);
  int byte_order = GetByteOrder();
  if (byte_order == LITTLEENDIAN) {
    
  }
  igmp_header->checksum = ntohs(igmp_header->checksum);
  igmp_header->address = nothl(igmp_header->address);
  

}
