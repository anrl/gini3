INCLUDES = -I$(top_srcdir)/include/wgini
LDADD = -lreadline -ltermcap -lslack -lpthread -lutil -lm
AM_CPPFLAGS = -DHAVE_GETOPT_LONG
bin_PROGRAMS = gwcenter
gwcenter_SOURCES = 802_11.c cli.c fading.c mathlib.c timer.c \
	          802_11_frame.c csma.c gwcenter.c mobility.c \
		antenna.c energy.c llc.c nomac.c vpl.c \
		awgn.c errmodel.c mac.c propagation.c wcard.c \
		channel.c event.c stats.c wirelessphy.c