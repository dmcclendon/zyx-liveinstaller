#
# Makefile for the ZyX Rebootless LivOS Installer
#

####################
# Global Variables #
####################
TOP         = .
include $(TOP)/build/makefile.common

###############
# Build Rules #
###############

default:
	make all

all:
	# it's python, nothing really to make

clean:
	# remove compiled files resulting from development testing
	find . -name "*.pyc" -exec rm -vf '{}' ';'

install:
	# XXX: install -D isn't sufficient??
	mkdir -p $(DESTDIR)/$(PREFIX)/bin
	mkdir -p $(DESTDIR)/$(PREFIX)/share/zyx-liveinstaller
	mkdir -p $(DESTDIR)/$(PREFIX)/share/applications
	mkdir -p $(DESTDIR)/etc/pam.d
	mkdir -p $(DESTDIR)/etc/security/console.apps
	mkdir -p $(DESTDIR)/$(PREFIX)/share/zyx-liveinstaller/ui
	mkdir -p $(DESTDIR)/$(PREFIX)/share/zyx-liveinstaller/pixmaps
	mkdir -p $(DESTDIR)/$(PREFIX)/share/doc/zyx-liveinstaller-$(VERSION)
	mkdir -p $(DESTDIR)/$(PYTHONDIR)/rli/
	# artwork
	$(INSTALL_DATA) -D \
		./art/banner.png \
		$(DESTDIR)/$(PREFIX)/share/zyx-liveinstaller/pixmaps/
	$(INSTALL_DATA) -D \
		./art/icon.png \
		$(DESTDIR)/$(PREFIX)/share/zyx-liveinstaller/pixmaps/
	# user interface specifications
	$(INSTALL_DATA) -D \
		./gui/zyx-liveinstaller.glade \
		$(DESTDIR)/$(PREFIX)/share/zyx-liveinstaller/ui/
	# desktop entry (_PROGRAM because its 755)
	$(INSTALL_PROGRAM) -D \
		./gui/zyx-liveinstaller.desktop \
		$(DESTDIR)/$(PREFIX)/share/applications/
	# automagic desktop icon facility
	# maybe bring back someday, but maybe not
#	$(INSTALL_PROGRAM) -D \
#		./gui/zz-zyx-liveinstaller.sh \
#		$(DESTDIR)/etc/X11/xinit/xinitrc.d/zz-zyx-liveinstaller.sh
	# documentation
	$(INSTALL_DATA) -D \
		./info/* \
		$(DESTDIR)/$(PREFIX)/share/doc/zyx-liveinstaller-$(VERSION)/
	$(INSTALL_DATA) -D \
		./AUTHORS \
		$(DESTDIR)/$(PREFIX)/share/doc/zyx-liveinstaller-$(VERSION)/
	$(INSTALL_DATA) -D \
		./COPYING \
		$(DESTDIR)/$(PREFIX)/share/doc/zyx-liveinstaller-$(VERSION)/
	$(INSTALL_DATA) -D \
		./README \
		$(DESTDIR)/$(PREFIX)/share/doc/zyx-liveinstaller-$(VERSION)/
	# python frontend
	$(INSTALL_PYTHON) -D \
		./gui/*.py \
		$(DESTDIR)/$(PYTHONDIR)/rli/
	# python backend helper / current cli
	$(INSTALL_PROGRAM) -D \
		./rli/zyx-liveinstaller-cli \
		$(DESTDIR)/$(PREFIX)/sbin/zyx-liveinstaller-cli
	# python backend
	$(INSTALL_PYTHON) -D \
		./rli/__init__.py \
		$(DESTDIR)/$(PYTHONDIR)/rli/
	$(INSTALL_PYTHON) -D \
		./rli/installer.py \
		$(DESTDIR)/$(PYTHONDIR)/rli/
	# precompile bytecode
	$(call COMPILE_PYTHON,$(DESTDIR)/$(PYTHONDIR)/rli)
	# priveledge handling 
	$(INSTALL) ./gui/zyx-liveinstaller.pam $(DESTDIR)/$(PAMD_DIR)/zyx-liveinstaller
	$(INSTALL) ./gui/zyx-liveinstaller.console $(DESTDIR)/$(SECURITY_DIR)/zyx-liveinstaller
	# launcher
	$(INSTALL_PROGRAM) -D \
		./gui/zyx-liveinstaller \
		$(DESTDIR)/$(PREFIX)/sbin/zyx-liveinstaller
	ln -s \
		consolehelper \
		$(DESTDIR)/$(PREFIX)/bin/zyx-liveinstaller
	

uninstall:
	rm -rvf $(DESTDIR)/$(PREFIX)/bin/zyx-liveinstaller
	rm -rvf $(DESTDIR)/$(PREFIX)/lib/zyx-liveinstaller
	rm -rvf $(DESTDIR)/$(PREFIX)/share/zyx-liveinstaller
	rm -rvf $(DESTDIR)/$(PREFIX)/share/doc/zyx-liveinstaller-$(VERSION)
	
tidy:
	@ echo "removing temporary and backup files"
	find . -name "*~" -exec rm -vf '{}' ';'
	find . -name "#*" -exec rm -vf '{}' ';'

release:
	@ echo "building release tarball"
	make distclean
	rm -rf /tmp/zyx-liveinstaller-*
	mkdir /tmp/zyx-liveinstaller-$(VERSION)
	cp -a ./* /tmp/zyx-liveinstaller-$(VERSION)/
	tar -C /tmp -cvjf \
		/tmp/zyx-liveinstaller-$(VERSION).tar.bz2 \
		./zyx-liveinstaller-$(VERSION)/
	mv /tmp/zyx-liveinstaller-$(VERSION).tar.bz2 ./
	rm -rf /tmp/zyx-liveinstaller-$(VERSION)/

xrelease:
	make release
	tar xvjf zyx-liveinstaller-$(VERSION).tar.bz2

distclean:
	make tidy
	make clean
	rm -f zyx-liveinstaller-$(VERSION)-$(RELEASE).src.rpm 
	rm -f zyx-liveinstaller-$(VERSION)-$(RELEASE).noarch.rpm 
	rm -f zyx-liveinstaller-$(VERSION).tar.bz2
	rm -f zyx-liveinstaller-$(VERSION)-$(RELEASE).sha512sums
	rm -rf zyx-liveinstaller-$(VERSION)

srpm:	
	rpmdev-setuptree
	make release
	cp zyx-liveinstaller-$(VERSION).tar.bz2 ${HOME}/rpmbuild/SOURCES/
	rpmbuild -bs build/zyx-liveinstaller.spec
	mv ${HOME}/rpmbuild/SRPMS/zyx-liveinstaller-$(VERSION)-$(RELEASE).src.rpm .

rpm:
	make srpm
	rpm -i zyx-liveinstaller-$(VERSION)-$(RELEASE).src.rpm 
	rpmbuild --rebuild zyx-liveinstaller-$(VERSION)-$(RELEASE).src.rpm 
	mv ${HOME}/rpmbuild/RPMS/noarch/zyx-liveinstaller-$(VERSION)-$(RELEASE).noarch.rpm .
	sha512sum zyx-liveinstaller-$(VERSION)-$(RELEASE).* > zyx-liveinstaller-$(VERSION)-$(RELEASE).sha512sums

vrepostuff:
	make rpm
	# this is for guitar-zyx (presently f10)
	cp -av zyx-liveinstaller-$(VERSION)-$(RELEASE).noarch.rpm ./vrepo/fedora/10/noarch/
	cp -av zyx-liveinstaller-$(VERSION)-$(RELEASE).src.rpm ./vrepo/fedora/10/SRPMS/
	cp -av zyx-liveinstaller-$(VERSION).tar.bz2 ./vrepo/tarballs/
	createrepo ./vrepo/fedora/10/noarch
	createrepo ./vrepo/fedora/10/SRPMS
