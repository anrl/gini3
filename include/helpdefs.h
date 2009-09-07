

#ifndef __HELPDEFINITIONS_H__
#define __HELPDEFINITIONS_H__

#define USAGE_IFCONFIG       "ifconfig action device [action specific options]"
#define USAGE_HELP           "help <command>"
#define USAGE_ROUTE          "route action [action specific options]"
#define USAGE_ARP            "arp action [action specific options]"
#define USAGE_VERSION        "version"
#define USAGE_SET            "set parameter [value]"
#define USAGE_HALT           "halt"
#define USAGE_EXIT           "exit"
#define USAGE_MTU            "mtu"
#define USAGE_SOURCE         "source filepath"
#define USAGE_PING           "ping [options] target"
#define USAGE_CONSOLE        "console [restart]"
#define USAGE_DISPLAY        "display [restart]"
#define USAGE_CLASSIFIER     "classifier qname [-src ip_spec [<min_port--max_port>]] [-dst ip_spec [<min_port--max_port>]] [-prot num] [-tos tos_spec]"
#define USAGE_FILTER     "filter qname [-src ip_spec [<min_port--max_port>]] [-dst ip_spec [<min_port--max_port>]] [-prot num] [-tos tos_spec]"

#define SHELP_IFCONFIG       "add, del, and modify interface information"
#define SHELP_HELP           "display help information on given command"
#define SHELP_ROUTE          "add, del, and modify the route information"
#define SHELP_ARP            "add, del, and modify ARP table information"
#define SHELP_VERSION        "get router version number"
#define SHELP_SET            "set control parameters"
#define SHELP_HALT           "halt the router"
#define SHELP_EXIT           "exit the command shell"
#define SHELP_MTU            "get the MTU value"
#define SHELP_SOURCE         "source filepath"
#define SHELP_PING           "ping another router or machine"
#define SHELP_CONSOLE        "manage port (FIFO) used to interact with wireshark"
#define SHELP_DISPLAY        "manage port (FIFO) used to interact with visualizer"
#define SHELP_CLASSIFIER     "add, del, and view classifier information"
#define SHELP_FILTER         "filter .."


/*
 * TODO: The long help descriptions should be revised with examples
 */

#define HELP_PREAMPLE        "These shell commands are defined internally.  Type `help' to see \n\
this list. Type `help name' to find out more about the function `name'.\n\
Because the GINI shell uses the underlying Linux shell to run \n\
commands not recognized by it, most Linux commands can be accessed \n\
from this shell. If GINI shell reimplements a Linux command \n\
(e.g., ifconfig), then only GINI version can be accessed from the\n\
GINI shell. To access the Linux version, find the actual location\n\
of the Linux command (i.e., whereis ifconfig) and give the \n\
absolute path (e.g., /sbin/ifconfig). \n"

#define LHELP_HELP           "\tDisplay helpful information about builtin commands.  If <command> is\n\
\tspecified, gives detailed help on all commands matching <command>,\n\
\totherwise a list of the builtins is printed.\n"

#define LHELP_IFCONFIG     "\tIfconfig is used to setup the router resident interfaces at bootup.\n\
\tAfter that it is normally used for tuning the setup or debugging the router interfaces.\n\
\tThis command can add, delete, or change interface parameters.\n\
           \n\
\tifconfig add eth0 -socket socketfile -addr IP_addr -network IP_network \n\
\t\t\t-hwaddr MAC [-gateway GW] [-mtu N] \n\
           \n\
\tThe above command can be used to add an interface. The socket is opened in client mode by\n\
\tthe ifconfig command. Therefore, the socket file should be already present (i.e., a switch\n\
\tshould have already created it for the router to connect. The server mode connection is yet\n\
\tto be implemented\n\
           \n\
\tifconfig del eth0 \n\
\tThe above configuration shuts down the interface and removes it.\n\
           \n\
\tifconfig show [brief|verbose] \n\
\tifconfig up eth0\n\
\tifconfig down eth0 \n\
\tifconfig mod eth0 (-gateway GW | -mtu N)\n"

#define LHELP_ROUTE          "\tRoute modifies the routing table within the router. It is meant to \n\
\tsetup the static routes within the router. This command should be used after the interfaces are \n\
\tsetup using the ifconfig command. The route command can be used to add, delete, and print the \n\
\trouting table.\n\
               \n\
\troute show \n\
\troute add -dev eth0 -net nw_addr -netmask mask [-gw gw_addr] \n\t\
\troute del route_number\n"

#define LHELP_ARP            "\tArp manipulates the router's ARP cache. In particular, it allows\n\
\tprinting the arp table and deleting the ARP entries. This is useful for debugging purposes.\n\
\n\
\tarp show \n\
\tarp show -ip ip_addr \n\
\tarp del \n\
\tarp del -ip ip_addr \n"

#define LHELP_VERSION        "\tShows the version information of the router."

#define LHELP_SET            "\tThis command is used to set global parameter values.\n\
\tCurrently, this command can be used to change verbose levels of the router and\n\
\tscheduling cycle length.\n\
\tTo display the current verbosity level use the following command:\n\
\tset verbose\n\
To change the current verbosity level to (say level 4), use the following command:\n\
\tset verbose 4\n\
\tSimilarly, to set the scheduling cycle length, use the following command:\n\
\tset sched-cycle 50000\n"

#define LHELP_PING           "\tPing sends an ICMP ECHO request message to the given target.\n\
\tIf the network connectivity is present and the target is up and running, it should respond\n\
\tto the message with an ECHO reply message. The ping command will send the ECHO messages\n\
\tin predefined intervals and measure the performance.\n\
         \n\
\tping target_IP\t sends 3 ICMP ping packets to the target.\n\
\tping -n target IP\t sends n ICMP ping packets to the target.\n"

#define LHELP_HALT           "\tHalts the router."

#define LHELP_MTU            "\tDisplays the MTU table for the configured interfaces."

#define LHELP_SOURCE         "\tThe source command is used to read a batch file and execute it.\n\
\tThis is useful to run initial setup commands without typing them one by one in the command shell\n"

#define LHELP_EXIT           "\tExit the command shell without halting the router. The router\n\
\tshould go into the deamon once the CLI is exitted."

#define LHELP_CONSOLE          "\tUse this command to manage the port used to connect to the wireshark\n\
\tWhen the gRouter starts, it automatically creates a FIFO under the name router_name.port in the\n\
in the home directory. You can connect a wireshark packet visualizer using the following command:\n\
\t wireshark -S -l -k -i router_name.port         \n\
Once the wireshark is started, it should remain connected to the gRouter until the gRouter halts.\n\
If the wireshark is stopped or the capturing process is stopped, the connection between the gRouter\n\
and the wireshark will terminate. If you want to reconnect the wireshark, the console should be \n\
restarted with the command: \"console restart\". Once the console is restarted, connect the wireshark\n\
again to the gRouter using the command originally used to connect. The packet capture should work now.\n"

#define LHELP_DISPLAY          "\tUse this command to manage the port used to connect to the information display\n\
\tThis port is responsible for connecting the gRouter to the external performance visualizer.\n\
To restart the diplay process which is necessary in the event of a router crash, use the following\n\
command \"display restart\"."

#define LHELP_FILTER       "\t .. "

#define LHELP_CLASSIFIER    "\tUse this command to create new classifier rules. A queue with the given name is\n\
\tcreated and is associated with the given rule. A rule can be defined using a 6-tuple. For example,\n\
\tto capture all packets coming from the subnet 192.168.5/24, define the following rule:\n\
\tclassifier add queue1 -src 192.168.5.0/24\n\
\tThe above command creates a new queue with the name \"queue1\" and sends all packets originating from\n\
the 192.168.5/24 subnet to that queue. Similarly, we can use destination networks, protocol numbers, type of service\n\
specifications as well in the rule. In certain cases (with the protocol defined such as TCP or UDP), we might \n\
want to use port numbers in the specifications as well. For example, we could use the following command to denote\n\
all port 80 TCP packets coming from subnet 192.197.121/24\n\
\t classifier add queue2 -src 192.197.121.0/24<80-80> -prot 6\n"

#endif


