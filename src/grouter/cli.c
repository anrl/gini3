/*
 * cli.c (Command line handler for the GINI router)
 * This file contains the functions that implement the CLI.
 * AUTHOR: Original version written by Weiling Xu
 *         Revised by Muthucumaru Maheswaran
 * DATE:   Revised on December 24, 2004 
 *
 * The CLI is used as a configuration file parser
 * as well. Right now the CLI module is only capable
 * of parsing a very simple format and limited command set...
 * Future development should make the CLI more versatile?
 * The CLI defers unknown command to the UNIX system at this point.
 */

#include "helpdefs.h"
#include "cli.h"
#include "gnet.h"
#include "grouter.h"
#include <stdio.h>
#include <strings.h>
#include "grouter.h"
#include "routetable.h"
#include "mtu.h"
#include "message.h"
#include "classifier.h"
#include "classspec.h"
#include "packetcore.h"
#include <slack/err.h>
#include <slack/std.h>
#include <slack/prog.h>
#include <slack/err.h>
#include <stdlib.h>
#include <readline/readline.h>
#include <readline/history.h>


Map *cli_map;
Mapper *cli_mapper;
static char *cur_line = (char *)NULL;       // static variable for holding the line

extern FILE *rl_instream;
extern router_config rconfig;

extern route_entry_t route_tbl[MAX_ROUTES];
extern mtu_entry_t MTU_tbl[MAX_MTU];
extern classifier_t *pktclassifier;
extern classifier_t *pktfilter;
extern pktcore_t *pcore;


int CLIInit(router_config *rarg)
{
	int stat, *jstat;

        if (!(cli_map = map_create(free)))
		return EXIT_FAILURE;

	// Disable certain signals..
	redefineSignalHandler(SIGINT, dummyFunction);
	redefineSignalHandler(SIGQUIT, dummyFunction);
	redefineSignalHandler(SIGTSTP, dummyFunction);

	verbose(2, "[cliHandler]:: Registering CLI commands in the command table ");
	// register all the commands here...
	registerCLI("help", helpCmd, SHELP_HELP, USAGE_HELP, LHELP_HELP);
	registerCLI("version", versionCmd, SHELP_VERSION, USAGE_VERSION, LHELP_VERSION);
	registerCLI("set", setCmd, SHELP_SET, USAGE_SET, LHELP_SET);
	registerCLI("ifconfig", ifconfigCmd, SHELP_IFCONFIG, USAGE_IFCONFIG, LHELP_IFCONFIG);
	registerCLI("halt", haltCmd, SHELP_HALT, USAGE_HALT, LHELP_HALT);
	registerCLI("route", routeCmd, SHELP_ROUTE, USAGE_ROUTE, LHELP_ROUTE);
	registerCLI("arp", arpCmd, SHELP_ARP, USAGE_ARP, LHELP_ARP);
	registerCLI("mtu", mtuCmd, SHELP_MTU, USAGE_MTU, LHELP_MTU);
	registerCLI("source", sourceCmd, SHELP_SOURCE, USAGE_SOURCE, LHELP_SOURCE);
	registerCLI("ping", pingCmd, SHELP_PING, USAGE_PING, LHELP_PING);
	registerCLI("console", consoleCmd, SHELP_CONSOLE, USAGE_CONSOLE, LHELP_CONSOLE);
	registerCLI("display", displayCmd, SHELP_DISPLAY, USAGE_DISPLAY, LHELP_DISPLAY);
	registerCLI("classifier", classifierCmd, SHELP_CLASSIFIER, USAGE_CLASSIFIER, LHELP_CLASSIFIER);
	registerCLI("filter", filterCmd, SHELP_FILTER, USAGE_FILTER, LHELP_FILTER);

	if (rarg->config_dir != NULL)
		chdir(rarg->config_dir);                  // change to the configuration directory
	if (rarg->config_file != NULL)
	{
		FILE *ifile = fopen(rarg->config_file, "r");
		rl_instream = ifile;              // redirect the input stream
		CLIProcessCmds(ifile, 0); 
		rl_instream = stdin;
	}
	
	if (rarg->cli_flag != 0)
		stat = pthread_create((pthread_t *)(&(rarg->clihandler)), NULL, CLIProcessCmdsInteractive, (void *)stdin);
	
	pthread_join(rarg->clihandler, (void **)&jstat);
	verbose(2, "[cliHandler]:: Destroying the CLI datastructures ");
	CLIDestroy();
}


void *CLIProcessCmdsInteractive(void *arg)
{
	FILE *fp = (FILE *)arg;
	CLIProcessCmds(fp, 1);
}



/*
 * managing the signals: first an ignore function.
 */
void dummyFunction(int sign)
{
	printf("Signal [%d] is ignored \n", sign);
}




void parseACLICmd(char *str)
{
	char *token;
	cli_entry_t *clie;
	char orig_str[MAX_TMPBUF_LEN];

	strcpy(orig_str, str);
	token = strtok(str, " \n");	
	if ((clie = map_get(cli_map, token)) != NULL)
		clie->handler((void *)clie);
	else
		system(orig_str);

}


void CLIPrintHelp()
{
	cli_entry_t *clie;

	printf("\nGINI Router Shell, version: %s", prog_version());
	printf("\n%s\n", HELP_PREAMPLE);

	if (!(cli_mapper = mapper_create(cli_map)))
	{
		map_destroy(&cli_map);
		return;
	}
        while (mapper_has_next(cli_mapper) == 1)
        {

		const Mapping *cli_mapping = mapper_next_mapping(cli_mapper);

		clie = (cli_entry_t *)mapping_value(cli_mapping);
		printf("%s:: \t%s\n\t%s\n", clie->keystr, clie->usagestr, 
		       clie->short_helpstr);
        }

}


/*
 * Read a string, and return a pointer to it.
 * Returns NULL on EOF.
 */
char *rlGets(int online)
{
	char prompt[MAX_TMPBUF_LEN];

	if (cur_line != NULL)
	{
		free (cur_line);
		cur_line = (char *)NULL;
	}

	sprintf(prompt, "GINI-%s $ ", rconfig.router_name);

	do
	{
		// Get a line from the user. 
		cur_line = readline(prompt);
	} while (online && (cur_line == NULL));

	// If the line has any text in it,
	// save it on the history. 
	if (cur_line && *cur_line)
		add_history (cur_line);

	return (cur_line);
}



/*
 * process CLI. The file pointer fp already points to an open stream. The
 * boolean variable online indicates whether processCLI is operating with
 * a terminal or from a batch input. For batch input, it should be FALSE.
 */

void CLIProcessCmds(FILE *fp, int online)
{
	int state = PROGRAM;
	char full_line[MAX_BUF_LEN];
	int lineno = 0;
	full_line[0] = '\0';

	// NOTE: the input stream for readline is already redirected
	// when processCLI is called from the "source" command.
	while ((cur_line = rlGets(online)) != NULL)
	{
		switch (state) 
		{
		case PROGRAM:
			if (cur_line[0] == CARRIAGE_RETURN)
				break;
			if (cur_line[0] == LINE_FEED)
				break;
			if (cur_line[0] == COMMENT_CHAR)
				state = COMMENT;
			else if ((strlen(cur_line) > 2) && (cur_line[strlen(cur_line)-2] == CONTINUE_CHAR))
			{
				state = JOIN;
				strcat(full_line, cur_line);
			}
			else
			{
				strcat(full_line, cur_line);
				if (strlen(full_line) > 0)
					parseACLICmd(full_line);
				full_line[0] = '\0';
			}
			lineno++;
			break;
		case JOIN:
			full_line[strlen(full_line)-2] = '\0';
			if (cur_line[strlen(cur_line)-2] == CONTINUE_CHAR)
				strcat(full_line, cur_line);
			else
			{
				state = PROGRAM;
				strcat(full_line, cur_line);
				if (strlen(full_line) > 0)
					parseACLICmd(full_line);
				full_line[0] = '\0';
			}
			break;
		case COMMENT:
			if (cur_line[0] != COMMENT_CHAR)
			{
				if (cur_line[strlen(cur_line)-2] == CONTINUE_CHAR)
				{
					state = JOIN;
					strcat(full_line, cur_line);
				} else
				{
					state = PROGRAM;
					strcat(full_line, cur_line);
					if (strlen(full_line) > 0)
						parseACLICmd(full_line);
					full_line[0] = '\0';
				}
			}
			break;
			lineno++;
		}
	}
}




void CLIDestroy()
{
	mapper_destroy(&cli_mapper);
        map_destroy(&cli_map);
}


void registerCLI(char *key, void (*handler)(), 
		 char *shelp, char *usage, char *lhelp)
{
	cli_entry_t *clie = (cli_entry_t *) malloc(sizeof(cli_entry_t));

	clie->handler = handler;
	strcpy(clie->long_helpstr, lhelp);
	strcpy(clie->usagestr, usage);
	strcpy(clie->short_helpstr, shelp);
	strcpy(clie->keystr, key);

	verbose(2, "adding command %s.. to cli map ", key);
	map_add(cli_map, key, clie);
	
}


/*------------------------------------------------------------------
 *               C L I  H A N D L E R S
 *-----------------------------------------------------------------*/


// some macro defintions...
#define GET_NEXT_PARAMETER(X, Y)           if (((next_tok = strtok(NULL, " \n")) == NULL) ||  \
                                             (strcmp(next_tok, X) != 0)) { error(Y); return; }; \
                                             next_tok = strtok(NULL, " \n")
#define GET_THIS_PARAMETER(X, Y)           if (((next_tok = strtok(NULL, " \n")) == NULL) ||  \
					       (strstr(next_tok, X) == NULL)) { error(Y); return; }


/*
 * Handler for the interface configuration command:
 * ifconfig add eth0 -socket socketfile -addr IP_addr -network IP_network -hwaddr MAC [-gateway GW] [-mtu N]
 * ifconfig del eth0
 * ifconfig show [brief|verbose]
 * ifconfig up eth0
 * ifconfig down eth0
 * ifconfig mod eth0 (-gateway GW | -mtu N)
 */
void ifconfigCmd()
{
	char *next_tok;
	interface_t *iface;
	char dev_name[MAX_DNAME_LEN], con_sock[MAX_NAME_LEN];
	uchar mac_addr[6], ip_addr[4], gw_addr[4], network_addr[4];
	int mtu, interface, mode;        

	// set default values for optional parameters
	bzero(gw_addr, 4);
	mtu = DEFAULT_MTU;
	mode = NORMAL_LISTING;
		
	// we have already matched ifconfig... now parsing rest of the parameters.
	next_tok = strtok(NULL, " \n");

	if (next_tok == NULL)
	{
		printf("[ifconfigCmd]:: missing action parameter.. type help ifconfig for usage.\n");
		return;
	}
	if (!strcmp(next_tok, "add")) 
	{
		GET_THIS_PARAMETER("eth", "ifconfig:: missing interface spec ..");
		strcpy(dev_name, next_tok);
		interface = gAtoi(next_tok);

		GET_NEXT_PARAMETER("-socket", "ifconfig:: missing -socket spec ..");
		strcpy(con_sock, next_tok);

		GET_NEXT_PARAMETER("-addr", "ifconfig:: missing -addr spec ..");
		Dot2IP(next_tok, ip_addr);

		GET_NEXT_PARAMETER("-network", "ifconfig:: missing -network spec ..");
		Dot2IP(next_tok, network_addr);

		GET_NEXT_PARAMETER("-hwaddr", "ifconfig:: missing -hwaddr spec ..");
		Colon2MAC(next_tok, mac_addr);
			
		while ((next_tok = strtok(NULL, " \n")) != NULL)
			if (!strcmp("-gateway", next_tok))
			{
				next_tok = strtok(NULL, " \n");
				Dot2IP(next_tok, gw_addr);
			} else if (!strcmp("-mtu", next_tok))
			{
				next_tok = strtok(NULL, " \n");
				mtu = atoi(next_tok);
			}
		iface = GNETMakeInterface(con_sock, dev_name, mac_addr, ip_addr, mtu, 0);
		if (iface != NULL)
		{
			verbose(2, "[configureInterfaces]:: Inserting the definition in the interface table ");
			GNETInsertInterface(iface);
			addMTUEntry(MTU_tbl, iface->interface_id, iface->device_mtu, iface->ip_addr);
		}
	}
	else if (!strcmp(next_tok, "del")) 
	{
		GET_THIS_PARAMETER("eth", "ifconfig:: missing interface spec ..");
		strcpy(dev_name, next_tok);
		interface = gAtoi(next_tok);
		destroyInterfaceByIndex(interface);
		deleteMTUEntry(interface);
	}
	else if (!strcmp(next_tok, "up")) 
	{
		GET_THIS_PARAMETER("eth", "ifconfig:: missing interface spec ..");
		strcpy(dev_name, next_tok);
		interface = gAtoi(next_tok);
		upInterface(interface);

	}
	else if (!strcmp(next_tok, "down")) 
	{
		GET_THIS_PARAMETER("eth", "ifconfig:: missing interface spec ..");
		strcpy(dev_name, next_tok);
		interface = gAtoi(next_tok);
		downInterface(interface);
	}
	else if (!strcmp(next_tok, "mod")) 
	{
		GET_THIS_PARAMETER("eth", "ifconfig:: missing interface spec ..");
		strcpy(dev_name, next_tok);
		interface = gAtoi(next_tok);

		while ((next_tok = strtok(NULL, " \n")) != NULL)
			if (!strcmp("-gateway", next_tok))
			{
				next_tok = strtok(NULL, " \n");
				strcpy(gw_addr, next_tok);
			} else if (!strcmp("-mtu", next_tok))
			{
				next_tok = strtok(NULL, " \n");
				mtu = atoi(next_tok);
			}

		changeInterfaceMTU(interface, mtu);
	} 
	else if (!strcmp(next_tok, "show")) 
	{
		if ((next_tok = strtok(NULL, " \n")) != NULL)
		{
			if (strstr(next_tok, "bri") != NULL)
				mode = BRIEF_LISTING;
			else if (strstr(next_tok, "verb") != NULL)
				mode = VERBOSE_LISTING;
		} else
			mode = NORMAL_LISTING;				

		printInterfaces(mode);
	}
	return;
}


/*
 * Handler for the connection "route" command
 * route show 
 * route add -dev eth0 -net nw_addr -netmask mask [-gw gw_addr]
 * route del route_number
 */
void routeCmd()
{
	char *next_tok;
	char tmpbuf[MAX_TMPBUF_LEN];
	uchar net_addr[4], net_mask[4], nxth_addr[4];
	int interface, del_route;
	char dev_name[MAX_DNAME_LEN];

	// set defaults for optional parameters
	bzero(nxth_addr, 4);

	next_tok = strtok(NULL, " \n");

	if (next_tok != NULL)
	{
		if (!strcmp(next_tok, "add")) 
		{
			GET_NEXT_PARAMETER("-dev", "route:: missing device name ..");
			strcpy(dev_name, next_tok);
			interface = gAtoi(next_tok);
			
			GET_NEXT_PARAMETER("-net", "route:: missing network address ..");
			Dot2IP(next_tok, net_addr);

			GET_NEXT_PARAMETER("-netmask", "route:: missing netmask ..");
			Dot2IP(next_tok, net_mask);

			verbose(2, "[routeCmd]:: Device %s Interface %d, net_addr %s, netmask %s ", 
			       dev_name, interface, IP2Dot(tmpbuf, net_addr), IP2Dot((tmpbuf+20), net_mask));

			if (((next_tok = strtok(NULL, " \n")) != NULL) &&
			    (!strcmp("-gw", next_tok)))
			{
				next_tok = strtok(NULL, " \n");
				Dot2IP(next_tok, nxth_addr);
			}
			addRouteEntry(route_tbl, net_addr, net_mask, nxth_addr, interface);
		}
		else if (!strcmp(next_tok, "del")) 
		{
			next_tok = strtok(NULL, " \n");
			del_route = gAtoi(next_tok);
			deleteRouteEntryByIndex(route_tbl, del_route);
		}
		else if (!strcmp(next_tok, "show")) 
			printRouteTable(route_tbl);
	}
	return;
}


char *parseIPSpec(char *instr, ip_spec_t *ips)
{
	char *nexttok;
	char *saveptr;
	int i = 3;
	
	nexttok = strtok_r(instr, ".", &saveptr);
	ips->ip_addr[i--] = atoi(nexttok);
	while(index(saveptr, '.'))
	{
		nexttok = strtok_r(NULL, ".", &saveptr);
		if (i >= 0)
			ips->ip_addr[i--] = atoi(nexttok);
		else
		{
			verbose(2, "wrong IP specification.. ");
			return NULL;
		}
	}
	if (index(saveptr, '/'))
	{
		nexttok = strtok_r(NULL, "/", &saveptr);	
		ips->ip_addr[i--] = atoi(nexttok);
	} else
		ips->ip_addr[i--] = 0;
	if ((strlen(saveptr) > 0) && (index(saveptr, '<') != saveptr))
	{
		nexttok = strtok_r(NULL, "<", &saveptr);
		if (strlen(nexttok) > 0)
			ips->preflen = atoi(nexttok);
	}
	return saveptr;
}


int parsePortRangeSpec(char *str, port_range_t *prs)
{
	char *token;

	if (strlen(str) > 0)
	{
		token = strsep(&str, "<->");
		if (strlen(token) > 0)
			prs->minport = atoi(token);
		token = strsep(&str, "<->");
		if (strlen(token) > 0)
			prs->maxport = atoi(token);
	}
}


/*
 * Classifier command:
 * classifier show
 * classifier add qname [-src ip_spec [<min_port--max_port>]] [-dst ip_spec [<min_port--max_port>]] [-prot num] [-tos tos_spec]
 * classifier del name
 */
void classifierCmd()
{
	char *next_tok, *remainstr;
	char tmpbuf[MAX_TMPBUF_LEN];
	char qname[MAX_DNAME_LEN];
	ip_spec_t ipss, ipsd;
	port_range_t prs, prd;
	int tos, prot;
	classrule_t *crule;
	simplequeue_t *qtoa;


	// set defaults for optional parameters
	bzero(&ipss, sizeof(ip_spec_t));
	bzero(&ipsd, sizeof(ip_spec_t));
	bzero(&prs, sizeof(port_range_t));
	bzero(&prd, sizeof(port_range_t));
	tos = 0;
	prot = 0;

	next_tok = strtok(NULL, " \n");

	if (next_tok != NULL)
	{
		if (!strcmp(next_tok, "add")) 
		{
			next_tok = strtok(NULL, " \n");
			strcpy(qname, next_tok);
			while ((next_tok = strtok(NULL, " \n")) != NULL)
			{
				if (!strcmp(next_tok, "-src"))
				{
					next_tok = strtok(NULL, " \n");
					remainstr = parseIPSpec(next_tok, &ipss);
					parsePortRangeSpec(remainstr, &prs);

				} else if (!strcmp(next_tok, "-dst"))
				{
					next_tok = strtok(NULL, " \n");
					remainstr = parseIPSpec(next_tok, &ipsd);
					parsePortRangeSpec(remainstr, &prd);

				} else if (!strcmp(next_tok, "-prot"))
				{
					next_tok = strtok(NULL, " \n");
					prot = atoi(next_tok);

				} else if (!strcmp(next_tok, "-tos"))
				{
					next_tok = strtok(NULL, " \n");
					tos = atoi(next_tok);
				} else 
				{
					error("[classifierCmd]:: unknown parameter in classifier add");
					return;
				}
			}
			// send the actual command to add the rule/queue.
			crule = createClassRule(&ipss, &ipsd, &prs, &prd, prot, tos);
			addRule(pktclassifier,  qname,  crule);
			addPktCoreQueue(pcore, qname, qname, 1.0);
			qtoa = getCoreQueue(pcore, qname);
			if (qtoa != NULL)
				addTarget(qname, qtoa);

		}
		else if (!strcmp(next_tok, "del")) 
		{
			next_tok = strtok(NULL, " \n");
			if (next_tok != NULL)
			{
				strcpy(qname, next_tok);
				delRule(pktclassifier, qname);
			}
		}
		else if (!strcmp(next_tok, "show")) 
		  printClassifier(pktclassifier);
	}
	return;
}


/*
 * filter command:
 * filter show
 * filter stats
 * filter add name [-src ip_spec [<min_port--max_port>]] [-dst ip_spec [<min_port--max_port>]] [-prot num] [-tos tos_spec]
 * filter del name
 */
void filterCmd()
{
	char *next_tok, *remainstr;
	char tmpbuf[MAX_TMPBUF_LEN];
	char fname[MAX_DNAME_LEN];
	ip_spec_t ipss, ipsd;
	port_range_t prs, prd;
	int tos, prot;
	classrule_t *frule;
	simplequeue_t *qtoa;


	// set defaults for optional parameters
	bzero(&ipss, sizeof(ip_spec_t));
	bzero(&ipsd, sizeof(ip_spec_t));
	bzero(&prs, sizeof(port_range_t));
	bzero(&prd, sizeof(port_range_t));
	tos = 0;
	prot = 0;

	next_tok = strtok(NULL, " \n");

	if (next_tok != NULL)
	{
		if (!strcmp(next_tok, "add")) 
		{
			next_tok = strtok(NULL, " \n");
			strcpy(fname, next_tok);
			while ((next_tok = strtok(NULL, " \n")) != NULL)
			{
				if (!strcmp(next_tok, "-src"))
				{
					next_tok = strtok(NULL, " \n");
					remainstr = parseIPSpec(next_tok, &ipss);
					parsePortRangeSpec(remainstr, &prs);

				} else if (!strcmp(next_tok, "-dst"))
				{
					next_tok = strtok(NULL, " \n");
					remainstr = parseIPSpec(next_tok, &ipsd);
					parsePortRangeSpec(remainstr, &prd);

				} else if (!strcmp(next_tok, "-prot"))
				{
					next_tok = strtok(NULL, " \n");
					prot = atoi(next_tok);

				} else if (!strcmp(next_tok, "-tos"))
				{
					next_tok = strtok(NULL, " \n");
					tos = atoi(next_tok);
				} else 
				{
					error("[filterCmd]:: unknown parameter in filter add");
					return;
				}
			}
			// send the actual command to add the rule/queue.
			frule = createClassRule(&ipss, &ipsd, &prs, &prd, prot, tos);
			addRule(pktfilter,  fname,  frule);
		}
		else if (!strcmp(next_tok, "del")) 
		{
			next_tok = strtok(NULL, " \n");
			if (next_tok != NULL)
			{
				strcpy(fname, next_tok);
				delRule(pktfilter, fname);
			}
		}
		else if (!strcmp(next_tok, "show")) 
		  printFilter(pktfilter);
		else if (!strcmp(next_tok, "stats")) 
		  printFilterStats(pktfilter);
	}
	return;
}



/*
 * Handler for the connection "arp" command:
 * arp show
 * arp show -ip ip_addr
 * arp del
 * arp del -ip ip_addr
 */
void arpCmd()
{
	char *next_tok;
	uchar mac_addr[6], ip_addr[4];

	next_tok = strtok(NULL, " \n");

	if (next_tok == NULL)
	{
		printf("[arpCmd]:: missing arp action.. type help arp for usage \n");
		return;
	}

	if (!strcmp(next_tok, "show")) 
	{
		if ((next_tok = strtok(NULL, " \n")) != NULL)
		{
			if (!strcmp("-ip", next_tok))
			{
				next_tok = strtok(NULL, " \n");
				strcpy(ip_addr, next_tok);
			} 
		}
		ARPPrintTable();
	} else if (!strcmp(next_tok, "del"))
	{
		if ((next_tok = strtok(NULL, " \n")) != NULL)
		{
			if (!strcmp("-ip", next_tok))
			{
				next_tok = strtok(NULL, " \n");
				strcpy(ip_addr, next_tok);
			} 
		}
		ARPDeleteEntry(ip_addr);
	}
}



void versionCmd()
{
	printf("\nGINI Router Version: %s \n\n", prog_version());
}



void haltCmd()
{
	verbose(1, "[haltCmd]:: Router %s shutting down.. ", prog_name());
	raise(SIGUSR1);
}


/*
 * send a ping packet...
 * ping [-num] IP_addr [-size payload size]
 */

void pingCmd()
{
	char *next_tok = strtok(NULL, " \n");
	int tries, pkt_size;
	uchar ip_addr[4];
	char tmpbuf[MAX_TMPBUF_LEN];

	if (next_tok == NULL)
		return;

	if (next_tok[0] == '-')
	{
		tries = gAtoi(next_tok);
		next_tok = strtok(NULL, " \n");
	} else
		tries = 1;
	Dot2IP(next_tok, ip_addr);
	verbose(2, "[pingCmd]:: ping command sent, tries = %d, IP = %s",
		tries, IP2Dot(tmpbuf, ip_addr));

	if ((next_tok = strtok(NULL, " \n")) != NULL)
	{
		if (!strcmp(next_tok, "-size"))
		{
			next_tok = strtok(NULL, " \n");
			pkt_size = atoi(next_tok);
		} else
			pkt_size = 64;
	} else
		pkt_size = 64;
	ICMPDoPing(ip_addr, pkt_size, tries);
}


void setCmd()
{
	char *next_tok = strtok(NULL, " \n");
	int level, cyclelen;

	if (next_tok == NULL)
	{
		error("[setCmd]:: ERROR!! missing set-parameter... ");
		return;
	}
	if (!strcmp(next_tok, "sched-cycle"))
	{
		if ((next_tok = strtok(NULL, " \n")) != NULL)
		{
			cyclelen = atoi(next_tok);
			if (cyclelen >=0)
				rconfig.schedcycle = cyclelen;
			else
				verbose(1, "ERROR!! schedule cycle length should be positive \n");
		} else
			printf("\nCurrent schedule cycle length: %d (microseconds) \n", rconfig.schedcycle);
	} else if (!strcmp(next_tok, "sched-policy"))
	{
		if ((next_tok = strtok(NULL, " \n")) != NULL)
		{
			strcpy(rconfig.schedpolicy, next_tok);
			if (!((!strcmp(rconfig.schedpolicy, "rr")) || (!strcmp(rconfig.schedpolicy, "wfq"))))
			{
				printf("Scheduling policy should be either rr or wfq: defaulting to rr\n");
				strcpy(rconfig.schedpolicy, "rr");
			}
		} else
			printf("\nCurrent scheduling policy: %s \n", rconfig.schedpolicy);
	} else if (!strcmp(next_tok, "verbose"))
	{
		if ((next_tok = strtok(NULL, " \n")) != NULL)
		{
			level = atoi(next_tok);
			if ((level >= 0) && (level <= 6))
				prog_set_verbosity_level(level);
			else
				verbose(1, "ERROR!! level should be in [0..6] \n");
		} else
			printf("\nCurrent verbose level: %d \n", prog_verbosity_level());
		
	} else 
		verbose(1, "ERROR!! Unknown option specified for set command");
}


void sourceCmd()
{
	FILE *fp;
	char *next_tok = strtok(NULL, " \n");

	if (next_tok == NULL)
	{
		error("[sourceCmd]:: ERROR!! missing file specification...");
		return;
	}
	
	if ((fp = fopen(next_tok, "r")) == NULL)
	{
		error("[sourceCmd]:: ERROR!! cannot open file %s.. ", next_tok);
		return;
	}

	rl_instream = fp;
	CLIProcessCmds(fp, 0);
	rl_instream = stdin;
}


/*
 * display the MTU table. This command does not allow any operations
 * on the MTU table. The MTU values are changed through the ifconfig command.
 */
void mtuCmd()
{
	char *next_tok;

	next_tok = strtok(NULL, " \n");

	if (next_tok == NULL)
	{
		printf("[mtuCmd]:: missing mtu action.. type help mtu for usage \n");
		return;
	}

	if (!strcmp(next_tok, "show")) 
		printMTUTable(MTU_tbl);
	else
		error("[mtuCmd]:: missing option -- show -- ");
}


void consoleCmd()
{
	char *next_tok = strtok(NULL, " \n");

	if (next_tok == NULL)
		consoleGetState();
	else if (!strcmp(next_tok, "restart"))
		consoleRestart(rconfig.config_dir, rconfig.router_name);
	else
	{
		verbose(2, "[consoleCmd]:: Unknown port action requested \n");
		return;
	}
}


void displayCmd()
{
	char *next_tok = strtok(NULL, " \n");
	int updateinterval;
	int rawmode;

	if (next_tok == NULL)
		infoGetState();
	else if (!strcmp(next_tok, "raw-times"))
	{
		if ((next_tok = strtok(NULL, " \n")) != NULL)
		{
			rawmode = atoi(next_tok);
			if ((rawmode == 0) || (rawmode == 1))
				setTimeMode(rawmode);
		} else
			printf("\nRaw time mode: %s  \n", getUpdateInterval());
	}
	else if (!strcmp(next_tok, "update-delay"))
	{
		if ((next_tok = strtok(NULL, " \n")) != NULL)
		{
			updateinterval = atoi(next_tok);
			if (updateinterval >=2)
				setUpdateInterval(updateinterval);
			else
				verbose(1, "Invalid update interval.. setting failed.. \n");
		} else
			printf("\nCurrent update interval: %d (seconds) \n", getUpdateInterval());
	}
	else
	{
		printf("Valid options for display: restart, raw-times, update-delay (use 'help display') \n");
		return;
	}
}


void helpCmd()
{

	char *next_tok = strtok(NULL, " \n");
	cli_entry_t *n_clie;
	
	if (next_tok == NULL)
		CLIPrintHelp();
	else
	{
		n_clie = (cli_entry_t *)map_get(cli_map, next_tok);
		if (n_clie == NULL)
			printf("ERROR! No help for command: %s \n", next_tok);
		else
		{
			printf("\n%s:: %s\n", n_clie->keystr, n_clie->usagestr);
			printf("%s\n", n_clie->long_helpstr);
		}
	}
}
