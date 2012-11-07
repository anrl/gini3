
#ifndef __IGMP_H_
#define __IGMP_H_

#include <sys/types.h>
#include <stdint.h>
#include "grouter.h"
#include "message.h"
#include "simplequeue.h"

#define BIGENDIAN 1
#define LITTLEENDIAN 2

typedef struct _igmp_header_t {
  unsigned version : 4;
  unsigned type : 4;
  char unused;
  uint16_t checksum;
  uint32_t address;
}igmp_header_t;

#define IGMP_HEADER_SIZE (sizeof(igmp_header_t))


#endif
