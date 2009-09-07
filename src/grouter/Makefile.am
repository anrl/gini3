INCLUDES = -I$(top_srcdir)/include
LDADD = -lreadline -ltermcap -lslack -lpthread -lutil -lm
AM_CPPFLAGS = -DHAVE_GETOPT_LONG
bin_PROGRAMS = grouter
grouter_SOURCES = arp.c ethernet.c gnet.c ip.c message.c mtu.c \
		routetable.c vpl.c cli.c fragment.c packetcore.c\
		icmp.c grouter.c utils.c simplequeue.c classifier.c \
		console.c info.c roundrobin.c wfq.c filter.c

man_MANS = grouter.1
EXTRA_DIST = grouter.1
