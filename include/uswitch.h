/* uml_virtual_switch.c
 * program to simulate a switch for user-mode-linux instances
 */

/* the defines */

/* from <linux/if_ether.h> */
#define ETH_ALEN 6

#define MAX_REMOTE 8
#define HASH_SIZE 128
#define HASH_VAL 11
#define MAX_AGE 200
#define SWITCH_MAGIC 0xfeedface

enum request_type { REQ_NEW_CONTROL };

/* structs */

union sa {
  struct sockaddr *s;
  struct sockaddr_un *sun;
  struct sockaddr_in *sin;
};
    
struct packet {
  struct {
    unsigned char dst[ETH_ALEN];
    unsigned char src[ETH_ALEN];
    unsigned char prot[2];
  } header;
  unsigned char data[1500];
};

struct fd {
  int fh;
  struct port *rmport;
  struct fd *next;
  void (*handle)(int);
};

struct port {
  int id;
  struct port *next;
  union sa sa;
  int fh;
  void (*sender)(struct port *, struct packet *, int);
};

struct hash_entry {
  struct hash_entry *next;
  struct port *port;
  time_t last_seen;
  unsigned char mac[ETH_ALEN];
};

struct cleanup {
  struct cleanup *next;
  void (*prg)(void);
};
