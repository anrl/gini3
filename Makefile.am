SUBDIRS = src/grouter src/uswitch src/gloader src/gbuilder src/wgini kernel fs
EXTRA_DIST = include/*  fs/* kernel/*

install-data-hook:
	mkdir $(prefix)/data
	chmod 755 $(prefix)/data
	mkdir $(prefix)/tmp
	chmod 755 $(prefix)/tmp

uninstall-hook:
	rm $(bindir)/gloader
	rm $(bindir)/gbuilder
	rm $(bindir)/gwcenter
	rm $(datadir)/gbuilder -rf
	rm $(datadir)/gloader -rf
	rm $(prefix)/etc/gif -rf
