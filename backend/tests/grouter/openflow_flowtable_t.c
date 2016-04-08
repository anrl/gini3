#include "openflow_flowtable.h"
#include "mut.h"
#include <stdint.h>


#include "common_def.h"

extern void openflow_flowtable_set_defaults(void);
extern uint8_t openflow_flowtable_ip_compare(uint32_t ip_1, uint32_t ip_2,
        uint8_t ip_len);

TESTSUITE_BEGIN

TEST_BEGIN("Flowtable Modification")
	openflow_flowtable_init();
	ofp_flow_mod mod;
  uint16_t error_code, error_type;
  mod.flags = OFPFF_SEND_FLOW_REM;
	mod.command = OFPFC_ADD;
	mod.match.wildcards = OFPFW_ALL;
	mod.out_port = OFPP_NONE;

	openflow_flowtable_modify(&mod, &error_type, &error_code);
	openflow_flowtable_release();
TEST_END

TESTSUITE_END
