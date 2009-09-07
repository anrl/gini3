gbuilderdir = $(datadir)/gbuilder
EXTRA_DIST = *py gif/* Pmw/*

install-data-hook:
	cp -r $(srcdir) $(gbuilderdir)
	cp -r $(srcdir)/gif $(prefix)/etc/.
	chmod +x $(gbuilderdir)/gbuilder.py
	ln -s $(gbuilderdir)/gbuilder.py $(bindir)/gbuilder
	chmod +x $(gbuilderdir)/TaskManager.py
	ln -s $(gbuilderdir)/TaskManager.py $(bindir)/TaskManager
	chmod +x $(gbuilderdir)/Graph_Stats.py
	ln -s $(gbuilderdir)/Graph_Stats.py $(bindir)/Graph_Stats
	chmod +x $(gbuilderdir)/Wireless_Parser.py
	ln -s $(gbuilderdir)/Wireless_Parser.py $(bindir)/Wireless_Parser
