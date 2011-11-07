#############################################################################
#############################################################################
##
## installer.py : ZyXLiveInstaller main class
##
##  Copyright 2009, Douglas McClendon <dmc AT viros DOT org>
##
#############################################################################
#############################################################################


#############################################################################
#############################################################################
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 3 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Library General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.
#
#############################################################################
#############################################################################


#############################################################################
#############################################################################
##
## developer tree detection and setup
##
#############################################################################
#############################################################################

#
# setup application specific python module/package search path
#

# for os.path
import os
# for sys.path
import sys
# for string.join
import string

# get absolute directory of the running code file
__abs_dir = os.path.dirname(os.path.abspath(__file__))

# check if this was invoked from a development tree
if os.path.exists(__abs_dir + "/../gui"):
    __developer_tree = True
else:
    __developer_tree = False

if __developer_tree is True:
    _ext_installer_dir=__abs_dir
else:
    _ext_installer_dir="/usr/sbin"


#############################################################################
#############################################################################
##
## libraries
##
#############################################################################
#############################################################################

# for threading.Lock
import threading
# for time.sleep
import time
# for Popen
import subprocess
# for SIGKILL
import signal


#############################################################################
##
## ZyXLiveInstallerError class
##
#############################################################################
class ZyXLiveInstallerError(Exception):
    """An exception class for all ZyXLiveInstaller errors."""

    # installer is the gui object needed to display the error message
    def __init__(self, error_msg):
        # nothing custom here yet

        # finish with the base class initialization function
        Exception.__init__(self, error_msg)


#############################################################################
##
## ZyXLiveInstaller class
##
#############################################################################
# edunote: (object) forces 'newstyle' class, inheriting newstyleness from the
# edunote:     class 'object' which is pythons root progenitor.
class ZyXLiveInstaller(object):
    """A class for rebootless LiveOS installation.

    An instance of the this class will launch a process that will
    install the current running LiveOS from its 'Live' storage (i.e. 
    cdrom+ram or usbstick) to one or more system storage volumes (i.e.
    disk partition or whole devices.)

    This is the virtual class, which distro-specific subclasses inherit 
    from, and provide real implementations of.
    """

    ##
    ## initialization
    ##
    
    def __init__(self, 
                 root_device="none",
                 boot_device="none",
                 swap_device="none",
                 ):

        # check for zyx vs f11 LiveOS
        if os.path.exists("/etc/zyx-release"):
            self.ext_backend_filename = "zyx-liveinstaller-cli"
        elif os.path.exists("/etc/fedora-release"):
            # currently z-l-c handles both zyx and fedora style LiveOS fs layouts
            self.ext_backend_filename = "zyx-liveinstaller-cli"
        elif os.path.exists("/etc/redhat-release"):
            self.ext_backend_filename = "zyx-liveinstaller-cli"
        else:
            raise ZyXLiveInstallerError("unknown/unsupported LiveOS distro")
        
        self.root_device = root_device
        self.boot_device = boot_device
        self.swap_device = swap_device

        # global progress status variable, can be polled to update
        # user feedback
        self.progress = 0.0
        self.progress_lock = threading.Lock()

        # initialize abortion mechanism
        # edunote: Python threads are not easily killable, so you
        # edunote: have to do something like this to watch for 
        # edunote: a requested death.
        self.request_installation_abort_flag = False
        self.request_installation_abort_flag_lock = threading.Lock()

    # run the (temporary) external installer backend
    def run_ext_installer(self):

        # initialize exception return value
        self.error_message = "none"

        ext_installer_exe = _ext_installer_dir + "/" + self.ext_backend_filename

        # bufsize=1 means line buffered
        self.ext_installer_proc = subprocess.Popen([ext_installer_exe, 
                                                    self.root_device,
                                                    self.boot_device,
                                                    self.swap_device],
                                                   stderr=subprocess.STDOUT,
                                                   stdout=subprocess.PIPE,
                                                   bufsize=1)

        while True:
            # read new lines of input until...
            outline = self.ext_installer_proc.stdout.readline()
            # ... the external backend process terminates
            if self.ext_installer_proc.poll() is not None:
                break
            # catch outline that matches 'error' and propogate exception
            # note: the use using error_message to pass the actual raising
            #       of the exception to the main thread
            if outline.find("error:") != -1:
                self.error_message = outline
                break
                
            # if the output line is progress status, update self.progress
            if outline.find("installation progress - ") != -1:
                # since this is the only writer to self.progress, the
                # lock may be pointless
                self.progress_lock.acquire()
                try:
                    last_progress = (float(outline.split()[4]) / 100)
                except:
                    self.error_message = \
                        "bad progress line: " + outline
                    break
                # due to float precision, we don't want to trigger an
                # assert on the progressbar being '>' 1.0
                if last_progress >= 0.9999:
                    self.progress = 0.999
                else:
                    self.progress = last_progress
                self.progress_lock.release()

    def do_install(self):
        """Execute the rebootless installation with the established parameters.

        This is a virtual/bogus implementation for testing purposes.  Distro-
        specific subclasses will have their own implementations.

        """


        # create external installer backend thread
        self.ext_installer_thread = \
            threading.Thread(target=self.run_ext_installer)
        # start external installer
        self.ext_installer_thread.start()

        xdone = False
        while xdone is not True:
            # check for user request to abort installation
            if self.request_installation_abort_flag is True:
                # terminate the external installer
                # python 2.6 
                #self.ext_installer_proc.terminate()
                os.kill(self.ext_installer_proc.pid,
                        signal.SIGKILL)
                # reset all state (for now just this)
                self.progress = 0.0
                self.request_installation_abort_flag = False
                # return failure
                return False

            self.ext_installer_thread.join(1.0)
            if self.ext_installer_thread.isAlive() is False:
                if self.error_message is not "none":
                    raise ZyXLiveInstallerError( \
                        "installer backend failed: " +
                        self.error_message)
                if self.progress <= 0.998:
                    raise ZyXLiveInstallerError( \
                        "installer backend failed to complete, last " +
                        "progress was " + str(self.progress))
                return True

    def request_installation_abort(self):
        # reviewer: since this is the only writer of _flag, and this will
        #           only ever be in one thread, is the locking required?
        self.request_installation_abort_flag_lock.acquire()
        self.request_installation_abort_flag = True
        self.request_installation_abort_flag_lock.release()
