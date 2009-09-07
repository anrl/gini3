gloaderdir = $(datadir)/gloader
gloader_DATA = gini_nw.py program.py utilities.py gini_components.py  gloader.py xml_processor.py gdist.py starter.py
sysconf_DATA = gloader.dtd
EXTRA_DIST = gini_nw.py program.py utilities.py gini_components.py  gloader.py xml_processor.py starter.py gdist.py gloader.dtd gloader.1

man_MANS = gloader.1

install-data-hook:
	chmod +x $(gloaderdir)/gloader.py
	ln -s $(gloaderdir)/gloader.py $(bindir)/gloader
	chmod +x $(gloaderdir)/gdist.py
	ln -s $(gloaderdir)/gdist.py $(bindir)/gdist



