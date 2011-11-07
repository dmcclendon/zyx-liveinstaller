Name:           zyx-liveinstaller
Version:        0.2.4
Release:        1
Summary:        Install a running LiveOS rebootlessly

Group:          Applications/System
License:        GPLv3
URL:            http://cloudsession.com/dawg/projects/zyx-liveinstaller
Source0:        http://cloudsession.com/dawg/downloads/%{name}/%{name}-%{version}.tar.bz2
#Patch0:        zyx-liveinstaller-0.1-random.patch

%{!?python_sitelib: %global python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print get_python_lib()")}

BuildArch:      noarch
BuildRequires:  desktop-file-utils
BuildRequires:  python-devel
Requires:       usermode

#
# dmc
#
Buildroot:	 %{_tmppath}/%{name}-%{version}-%{release}-root
Requires:	 python
#Prereq: 
BuildPrereq:	 make
# XXX: author's build infrastructure (f10 for f11+,centos,soas)
# ???: can anyone tell me a more appropriate way to build a package
#      for systems with python 2.4 vs 2.5 vs 2.6, than all the XXXs?
AutoReq: 0


%description
ZyX-LiveInstaller will perfrom a traditional LiveOS installation,
however instead of installing a fresh copy of the LiveOS to disk
to be used on the next reboot, it live migrates the running LiveOS's
root filesystem to disk.  In this fashion it does not require a
reboot to begin using the installed system.


%prep
%setup -q


%build
make %{?_smp_mflags}


%install
rm -rf $RPM_BUILD_ROOT
make install DESTDIR=$RPM_BUILD_ROOT
desktop-file-validate $RPM_BUILD_ROOT/%{_datadir}/applications/zyx-liveinstaller.desktop

# XXX: for centos
if [ "$RPM_BUILD_ROOT/%{python_sitelib}" != "$RPM_BUILD_ROOT/%{_libdir}/python2.4/site-packages" ]; then
    mkdir -p $RPM_BUILD_ROOT/%{_libdir}/python2.4/site-packages/rli
    for file in $( ls -1A "$RPM_BUILD_ROOT/%{python_sitelib}/rli" ); do
        ln -s "%{python_sitelib}/rli/${file}" \
            "$RPM_BUILD_ROOT/%{_libdir}/python2.4/site-packages/rli/" 
    done
fi

# XXX: for soas
if [ "$RPM_BUILD_ROOT/%{python_sitelib}" != "$RPM_BUILD_ROOT/%{_libdir}/python2.6/site-packages" ]; then
    mkdir -p $RPM_BUILD_ROOT/%{_libdir}/python2.6/site-packages/rli
    for file in $( ls -1A "$RPM_BUILD_ROOT/%{python_sitelib}/rli" ); do
        ln -s "%{python_sitelib}/rli/${file}" \
            "$RPM_BUILD_ROOT/%{_libdir}/python2.6/site-packages/rli/" 
    done
fi


%clean
rm -rf $RPM_BUILD_ROOT


%post

# if this is a runtime install, copy .desktop file into place since
# clearly the user is interested in this experimental software
#
# note, unlike fedora/anaconda/liveinst, this is not done by default
# if the package was installed during LiveOS mastering, due to the
# experimental nature.  Also for zyx I don't start nautilus on the
# desktop by default anyway
if [ -d /home/liveuser/Desktop ]; then
    cp /usr/share/applications/zyx-liveinstaller.desktop \
        /home/liveuser/Desktop \
	> /dev/null 2>&1
    chown liveuser:liveuser \
        /home/liveuser/Desktop/zyx-liveinstaller.desktop \
	> /dev/null 2>&1
    chmod 755 \
        /home/liveuser/Desktop/zyx-liveinstaller.desktop \
	> /dev/null 2>&1
fi

# and for CentOS
if [ -d /home/centos/Desktop ]; then
    cp /usr/share/applications/zyx-liveinstaller.desktop \
        /home/centos/Desktop \
	> /dev/null 2>&1
    chown centos:centos \
        /home/centos/Desktop/zyx-liveinstaller.desktop \
	> /dev/null 2>&1
    chmod 755 \
        /home/centos/Desktop/zyx-liveinstaller.desktop \
	> /dev/null 2>&1
fi
      

%preun


%postun


%files
%defattr(-,root,root,-)
%doc AUTHORS COPYING README
%{_bindir}/%{name}
%{_datadir}/%{name}/
%{_sbindir}/*
%{python_sitelib}/rli/
%attr(0644,root,root) %{_datadir}/applications/%{name}.desktop
%attr(0644,root,root) %config(noreplace) /etc/pam.d/%{name}
%attr(0644,root,root) %config(noreplace) /etc/security/console.apps/%{name}
# maybe someday, but probably not
#/etc/X11/xinit/xinitrc.d/zz-zyx-liveinstaller.sh
# XXX: for centos
%{_libdir}/python2.4/site-packages/rli/
# XXX: for f12/soas
%{_libdir}/python2.6/site-packages/rli/


%changelog

* Thu May 06 2010 Douglas McClendon <dmc@cloudsession.com> - 0.2.4-1
- newer kernels require a new procedure for snapshot handling

* Fri Feb 12 2010 Douglas McClendon <dmc@viros.org> - 0.2.3-1
- enhancement: use /etc/zyx-liveinstaller.banner.png if it exists
- bugfix: tmpfs symlinks now owned by owner of their target
- update: mkinitramfs new syntax
- zyx: no tmpfs mounts like ancestor anymore

* Tue Jan 19 2010 Douglas McClendon <dmc@viros.org> - 0.2.2-1
- fix permissions on /tmp (had lost 777+t prior to subsequent reboot)
- zyx: copy music from livemedia to /usr/share/music
- zyx: leave autojam off of possible installed bootloader args/append

* Mon Dec 21 2009 Douglas McClendon <dmc@viros.org> - 0.2.1-1
- f11 based *zyx for the moment will do the extra tmpfs cruftage as well

* Tue Nov  9 2009 Douglas McClendon <dmc@viros.org> - 0.1.17-1
- bugfix: fstype-flag was not being set when target was sole partition
- bugfix: add recently required execute permission on .desktop file

* Tue Oct 27 2009 Douglas McClendon <dmc@viros.org> - 0.1.16-1
- build: incorporate several changes, noarch, from Sebastian Dziallas
- build: improve python version compatability tricks
  - bugfix: now upgrade from fedora build works
- typo: 'boot-(/)' -> 'boot-(/boot)'
- aesthetic: add installation choice information to install progress page
- aesthetic: remove unusable buttons for unfinished features
- aesthetic: don't show terminal output of partitioner
- bugfix: yes, there seems to have indeed been a bug with no-swap installs
  - bug reported by Tom Gilliard, fedora-bz-530787
- bugfix: centos: fixed failure to reboot when rootfs was on non-lvm 

* Sat Oct 24 2009 Douglas McClendon <dmc@viros.org> - 0.1.15-1
- enhancement: centos-5.4 support: py2.4, new distrotype, misc...
- enhancement: untested initial support for /dev/vd* devices
- bugfix: enforce target install volume size minimums

* Tue Oct 13 2009 Douglas McClendon <dmc@viros.org> - 0.1.14-1
- bugfix: handle nondefault kernel cmdline args
- debug: backend failure exception propogation tested and working
- bugfix: catch exception for situation with no /dev/disk/by-id
- bugfix: yes, there seems to have indeed been a bug with no-swap installs

* Thu Oct  8 2009 Douglas McClendon <dmc@viros.org> - 0.1.13-1
- bugfix: extra space caused problem with mitigating automounter
- bugfix: missed a few things related to v0.1.12 f12 udev config
  - should now be able to eject LiveCD after install of f12 based distro
- bugfix: randomize initial UUID to allow multiple concurrent installs
- bugfix: use blkid instead of deprecated vol_id (absent in f12)
- bugfix: newer udev path_id needs non /sys prefixed argument
- debug: catching more errors, and giving user better directions for feedback
- use rootfs type for bootfs unless f11 special case (that needs ext3)

* Mon Sep 21 2009 Douglas McClendon <dmc@viros.org> - 0.1.12-1
- cli: handle new lack of liveos udev rules in f12
- cli: handle dracut for initramfs in f12

* Thu Sep 03 2009 Douglas McClendon <dmc@viros.org> - 0.1.11-1
- cli: fix /boot partition boot and type flags not being set
  - thanks to feedback from Tom Gilliard
- cli: move to a consistent bash quoting style
- gui: correctly narrow check for f11 seperate /boot requirement
- gui: correctly disallow /boot on lvm
- gui: use /etc/zyx-liveinstaller.install.txt if available
- gui: abort after intro if already installed, with error page

* Sat Aug 15 2009 Douglas McClendon <dmc@viros.org> - 0.1.10-1
- move gui python to site-packages, for rpmlint
- renamed rliveinst.zyx to /usr/sbin/zyx-liveinstaller-cli
- e2label rootfs after installation to non-LiveOS label
- remove seperate boot requirement for f10/zyx
- UUID for /boot in fstab too, helps with hibernate

* Fri Jul 31 2009 Douglas McClendon <dmc@viros.org> - 0.1.9-1
- tweak stupid .present delay workaround (for Guitar-ZyX-0.3)
- catch stderr in /var/log/zyx-liveinstaller.log, and more debug output
- attempt to unmount targets that have been automounted under /media
- genericize attempted unmount of live-osimg-min automounted under /media

* Tue Jul 28 2009 Douglas McClendon <dmc@viros.org> - 0.1.8-1
- zyx only: minor typo, remove liveos lvm devices from list
- rework internal device representation, fixing pre-f11 lvm problem
- add temporary special case for soas live-osimg-min mounting oddity
- more info added to BUGS/FAQ/README

* Mon Jul 27 2009 Douglas McClendon <dmc@viros.org> - 0.1.7-1
- vastly improve FAQ

* Sat Jul 25 2009 Douglas McClendon <dmc@viros.org> - 0.1.6-1
- remove zyx special lvm names from list (like for f11)
- use UUID= in fstab and grub.config, primarily to make 
  grubby happy, but also for consistency with anaconda.
- remove attempted workaround of issue with pre-first-reboot 
  hibernate.  Until grub(?) bug fixed, user must work around 
  at the grub-prompt-instead-of-unhibernation by typing e.g.
  # assuming /boot is on /dev/sda1
  grub> root (hd0,0)
  grub> setup (hd0)
  grub> reboot
  :( sigh...

* Fri Jul 17 2009 Douglas McClendon <dmc@viros.org> - 0.1.5-1
- trying harder to deal with /tmp tmpfs
- noted grubby problems in BUGS

* Fri Jul 17 2009 Douglas McClendon <dmc@viros.org> - 0.1.4-1
- removed facility for launcher desktop icon from xinit,
  but changed .desktop so it is shown under System Tools.
- better/fixed freeing of livemedia resources
- desensitized incompletely implemented installation abort
- try to migrate f11 live-only tmpfs's to rootfs
- support rootfs and swap on lvm
- support wholedisk targets (still need choice exclusion logic)
- top review text now uses long device names rather than short
- output is now logged to /var/log/rliveinst.log
- support ZyX LiveOS again, for now, with same backend
- misc bugfixes and refactorings

* Mon Jul 13 2009 Douglas McClendon <dmc@viros.org> - 0.1.3-1
- workaround fedora/grub problem by disabling hibernate autoboot
  - which I never liked anyway

* Mon Jul 13 2009 Douglas McClendon <dmc@viros.org> - 0.1.2-1
- really fix the grub configuration

* Sun Jul 12 2009 Douglas McClendon <dmc@viros.org> - 0.1.1-1
- fixed bugs with grub configuration
- better banner png compression
- red highlights for unselectable volumes (due to prior selection)
- misc cleanups

* Mon Jul 06 2009 Douglas McClendon <dmc@viros.org> - 0.1-1
- initial release and packaging

