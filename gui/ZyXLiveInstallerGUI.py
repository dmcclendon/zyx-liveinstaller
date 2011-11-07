#############################################################################
#############################################################################
##
## installergui.py : ZyXLiveInstallerGUI main class
##
## Copyright 2009 Douglas McClendon <dmc AT viros DOT org>
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
## abbreviations (for code readability- you need to know these)
##
#############################################################################
#############################################################################
#
# rps -- Root Partition Selection
# bps -- Boot Partition Selection
# sps -- Swap Partition Selection


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
if __abs_dir.endswith("/gui"):
    _developer_tree = True
else:
    _developer_tree = False
    
if _developer_tree is True:
    # add devtree root path to python search path to find rli
    sys.path.insert(0, __abs_dir + "/..")
    # set up resource locations
    PIXMAPS_PATH = __abs_dir + "/../art"
    UI_PATH = __abs_dir
    DEVELOPER_DEBUG = True
else:
    # set up resource locations
    PIXMAPS_PATH = "/usr/share/zyx-liveinstaller/pixmaps"
    UI_PATH = "/usr/share/zyx-liveinstaller/ui"
    DEVELOPER_DEBUG = False
    

#############################################################################
#############################################################################
##
## constants
##
#############################################################################
#############################################################################

# resource files
LOGO_IMAGE = PIXMAPS_PATH + "/banner.png"
ICON_IMAGE = PIXMAPS_PATH + "/icon.png"
UI_SPEC = UI_PATH + "/zyx-liveinstaller.glade"

# TODO: file/fix glade-3 ui bug, in that it lets you set the visible
#       page to a higher value than the numpages property.

# from glade xml ui, main_notebook page values
MODES = {
    "error" : 0,
    "intro" : 1,
    "partitioner" : 2,
    "rps" : 3,
    "bps" : 4,
    "sps" : 5,
    "review" : 6,
    "installing" : 7,
    "success" : 8,
}


# period in ms for idle polling function
POLL_INTERVAL = 333


#############################################################################
#############################################################################
##
## libraries
##
#############################################################################
#############################################################################


# for commandline arguments, exit, ... 
import sys
# edunote: thread is the lower level interface, which seems to lack join(),
# edunote: and net wisdom is threading is effectively always the right choice.
import threading
# for gobject (treeviewmodel, threads_init...)
import gobject
# for various fs access, etc.
import os
# for spawning helper processes
import subprocess
# for simple extended widget text font properties
import pango
# for sleep
import time


try:
    # for gui
    import pygtk
    pygtk.require("2.0")
except:
    pass
try:
    # for gui
    import gtk
    # for rad gui
    import gtk.glade
except:
    sys.exit(1)

# for rebootless installer backend
import rli


#############################################################################
#############################################################################
##
## Class Definitions
##
#############################################################################
#############################################################################


#############################################################################
##
## ZyXLiveInstallerGUIError class
##
#############################################################################
class ZyXLiveInstallerGUIError(Exception):
    """An exception class for all ZyXLiveInstallerGUI errors."""

    # installer is the gui object needed to display the error message
    def __init__(self, installer, error_msg):
        gtk.gdk.threads_enter()
        try:
            # set the error_msg to be visible on the error mode/page
            installer.set_error_text(error_msg)
            # set the mode to the error page
            installer.set_mode("error")
        finally:
            gtk.gdk.threads_leave()
        # finish with the base class initialization function
        Exception.__init__(self, error_msg)


#############################################################################
##
## ZyX-LiveInstaller GUI class
##
#############################################################################
class ZyXLiveInstallerGUI(object):
    """A GUI for rebootless LiveOS installation.

    An instance of the this class will launch a GUI wizard allowing 
    a user to choose installation partition/volume options, and then 
    initiate a *Rebootless* LiveOS installation.  

    """

    ##
    ## initialization
    ##
    
    def __init__(self):
        # TODO: there is enough here readability wise to justify breaking
        #       all this up into a set of self.init_* functions
        
        #####################################################################
        ##
        ## pygtk-glade stuff
        ##
        #####################################################################

        ##
        ## basic gtk threading init (required)
        ##
        # edunote: from 
        # edunote: http://faq.pygtk.org/index.py?req=show&file=faq20.001.htp
        # edunote: "Other threads can do window modification, processing, 
        # edunote: etc. Each of those other threads needs to wrap any GTK+ 
        # edunote: method calls in a gtk.gdk.threads_enter() / 
        # edunote: gtk.gdk.threads_leave() pair. Preferably, this should be 
        # edunote: done in try..finally -- if you miss threads_leave() due 
        # edunote: to exception, your program will most likely deadlock."
        gobject.threads_init()

        ##
        ## pygtk-glade: load the glade designed gui 
        ##
        # TODO: catch exceptions
        self.gladefile = UI_SPEC
        self.wTree = gtk.glade.XML(self.gladefile)

        ##
        ## pygtk-glade: get needed global widget handles
        ##

        # TODO: eval loop, cough cough
        #       (would have to change a few widget names, i.e. _treeview)

        self.main_window = self.wTree.get_widget("main_window")
        self.main_notebook = self.wTree.get_widget("main_notebook")

        self.error = self.wTree.get_widget("error")
        self.error_logo = self.wTree.get_widget("error_logo")
        self.error_text = self.wTree.get_widget("error_text")

        self.intro = self.wTree.get_widget("intro")
        self.intro_logo = self.wTree.get_widget("intro_logo")
        self.intro_text = self.wTree.get_widget("intro_text")

        self.partitioner = self.wTree.get_widget("partitioner")
        self.partitioner_logo = self.wTree.get_widget("partitioner_logo")
        self.partitioner_text = self.wTree.get_widget("partitioner_text")

        self.rps = self.wTree.get_widget("rps")
        self.rps_logo = self.wTree.get_widget("rps_logo")
        self.rps_choices = self.wTree.get_widget("rps_choices_treeview")
        self.rps_button_next = self.wTree.get_widget("rps_button_next")

        self.bps = self.wTree.get_widget("bps")
        self.bps_logo = self.wTree.get_widget("bps_logo")
        self.bps_choices = self.wTree.get_widget("bps_choices_treeview")
        self.bps_button_next = self.wTree.get_widget("bps_button_next")

        self.sps = self.wTree.get_widget("sps")
        self.sps_logo = self.wTree.get_widget("sps_logo")
        self.sps_choices = self.wTree.get_widget("sps_choices_treeview")

        self.review = self.wTree.get_widget("review")
        self.review_logo = self.wTree.get_widget("review_logo")
        self.review_text = self.wTree.get_widget("review_text")

        self.installing = self.wTree.get_widget("installing")
        self.installing_logo = self.wTree.get_widget("installing_logo")
        self.installing_text = self.wTree.get_widget("installing_text")
        self.installing_progressbar = \
            self.wTree.get_widget("installing_progressbar")

        self.success = self.wTree.get_widget("success")
        self.success_logo = self.wTree.get_widget("success_logo")
        self.success_text = self.wTree.get_widget("success_text")

        # set the icon
        self.main_window.set_icon_from_file(ICON_IMAGE)

        # set to be maximized by default
        self.main_window.maximize()

        ##
        ## pygtk-glade: create GUI event signal handler dict and connect it
        ##
        # note: this is basically just a few windowmanagerish things, 
        #       followed by all the wizard buttons roughly in the order the 
        #       user would see them.(Though starting with the size_allocates)
        # TODO: as above, modes eval iteration for appropriate entries, or 
        #       alternate rework (i.e. size_allocate)
        signal_handler_mappings_hash = {
            "on_error_logo_size_allocate" : \
                self.on_logo_size_allocate,
            "on_intro_logo_size_allocate" : \
                self.on_logo_size_allocate,
            "on_partitioner_logo_size_allocate" : \
                self.on_logo_size_allocate,
            "on_rps_logo_size_allocate" : \
                self.on_logo_size_allocate,
            "on_bps_logo_size_allocate" : \
                self.on_logo_size_allocate,
            "on_sps_logo_size_allocate" : \
                self.on_logo_size_allocate,
            "on_review_logo_size_allocate" : \
                self.on_logo_size_allocate,
            "on_installing_logo_size_allocate" : \
                self.on_logo_size_allocate,
            "on_success_logo_size_allocate" : \
                self.on_logo_size_allocate,
            "on_main_window_destroy" : \
                self.on_main_window_destroy,
#            "on_main_window_configure_event" : \
#                self.on_main_window_configure_event,
            "on_error_button_exit_clicked" : \
                self.on_intro_button_exit_clicked,
            "on_intro_button_exit_clicked" : \
                self.on_intro_button_exit_clicked,
           "on_intro_button_partitioner_clicked" : \
                self.on_intro_button_partitioner_clicked,
            "on_intro_button_next_clicked" : \
                self.on_intro_button_next_clicked,
            "on_partitioner_button_exit_clicked" : \
                self.on_partitioner_button_exit_clicked,
            "on_partitioner_button_abort_clicked" : \
                self.on_partitioner_button_abort_clicked,
            "on_rps_button_exit_clicked" : \
                self.on_rps_button_exit_clicked,
            "on_rps_button_back_clicked" : \
                self.on_rps_button_back_clicked,
            "on_rps_button_next_clicked" : \
                self.on_rps_button_next_clicked,
            "on_bps_button_exit_clicked" : \
                self.on_bps_button_exit_clicked,
            "on_bps_button_back_clicked" : \
                self.on_bps_button_back_clicked,
            "on_bps_button_next_clicked" : \
                self.on_bps_button_next_clicked,
            "on_sps_button_exit_clicked" : \
                self.on_sps_button_exit_clicked,
            "on_sps_button_back_clicked" : \
                self.on_sps_button_back_clicked,
            "on_sps_button_next_clicked" : \
                self.on_sps_button_next_clicked,
            "on_review_button_exit_clicked" : \
                self.on_review_button_exit_clicked,
            "on_review_button_back_clicked" : \
                self.on_review_button_back_clicked,
            "on_review_button_next_clicked" : \
                self.on_review_button_next_clicked,
            "on_installing_button_abort_exit_clicked" : \
                self.on_installing_button_abort_exit_clicked,
            "on_installing_button_abort_back_clicked" : \
                self.on_installing_button_abort_back_clicked,
            "on_success_button_viewdocs_clicked" : \
                self.on_success_button_viewdocs_clicked,
            "on_success_button_done_clicked" : \
                self.on_success_button_done_clicked,
            }
        self.wTree.signal_autoconnect(signal_handler_mappings_hash)

        #####################################################################
        ##
        ## parse commandline
        ##
        #####################################################################
        # TODO: gui-less mode available from commandline
        #        if len(sys.argv) == 2:
        #            self.something = sys.argv[1]
        #        else:
        #            self.something = DEFAULT


        #####################################################################
        ##
        ## check for seperate /boot volume requirement
        ##
        #####################################################################
        self.must_have_seperate_boot = False
        if os.path.exists("/etc/fedora-release"):
            fedora_release = open("/etc/fedora-release")
            if fedora_release.readlines()[0].startswith("Fedora release 11 (Leonidas)") \
                    is True:
                self.must_have_seperate_boot = True
            # todo: close file? (this work?)
            fedora_release.close()
            
        #####################################################################
        ##
        ## initialize installation progress text
        ##
        #####################################################################
            
        if os.path.exists("/etc/zyx-liveinstaller.install.txt"):
            install_text_file = open("/etc/zyx-liveinstaller.install.txt")
            self.set_installing_text(install_text_file.read())

        self.install_text=(self.installing_text.get_buffer()).get_text( \
            (self.installing_text.get_buffer()).get_start_iter(),
            (self.installing_text.get_buffer()).get_end_iter())
            

        #####################################################################
        ##
        ## set up widget infrastructure 
        ##
        #####################################################################

        ##
        ## load the banner image into a GdkPixBuf to be shared by 
        ## the *_logo widgets
        ##

        if os.path.exists("/etc/zyx-liveinstaller.banner.png"):
            self.gpb = gtk.gdk.pixbuf_new_from_file(\
                "/etc/zyx-liveinstaller.banner.png")
        else:
            self.gpb = gtk.gdk.pixbuf_new_from_file(LOGO_IMAGE)

        self.gpb_aspect_ratio = (self.gpb.get_width() * 1.0) / \
            (self.gpb.get_height() * 1.0)

        # tell the app that the logo only really needs 1x1(560x420), thus can 
        # be sized that small by the user
        self.main_window.set_size_request(560, 420)
        self.main_notebook.set_size_request(560, 420)

        # force initial detection of new logo widget allocation w&h 
        # in signal handler
        self.logo_old_allocation_width = -1
        self.logo_old_allocation_height = -1

        # set the logo from the pixbuf
        # TODO: use eval iterator or alternate rework
        # TODO: check if these are causing slow startup on my aspire one
        self.error_logo.set_from_pixbuf(self.gpb)
        self.intro_logo.set_from_pixbuf(self.gpb)
        self.partitioner_logo.set_from_pixbuf(self.gpb)
        self.rps_logo.set_from_pixbuf(self.gpb)
        self.bps_logo.set_from_pixbuf(self.gpb)
        self.sps_logo.set_from_pixbuf(self.gpb)
        self.review_logo.set_from_pixbuf(self.gpb)
        self.installing_logo.set_from_pixbuf(self.gpb)
        self.success_logo.set_from_pixbuf(self.gpb)

        # set up various aspects of the multicolumn volume selection
        # widget used for root/boot/swap choice
        self.init_dest_vol_stuff()

        # set larger than default fonts on textview widgets
        self.error_text.modify_font(pango.FontDescription("Sans 12"))
        self.intro_text.modify_font(pango.FontDescription("Sans 12"))
        self.review_text.modify_font(pango.FontDescription("Sans 12"))
        self.installing_text.modify_font(pango.FontDescription("Sans 12"))
        self.success_text.modify_font(pango.FontDescription("Sans 12"))


        #####################################################################
        ##
        ## initialize global state
        ##
        #####################################################################

        # create an installer (the non-gui thing that does the real work)
        self.installer = rli.ZyXLiveInstaller()

        # find preferred external partitioner
        if os.path.exists("/usr/bin/palimpsest"):
            self.ext_partitioner = "/usr/bin/palimpsest"
        elif os.path.exists("/usr/bin/gparted"):
            self.ext_partitioner = "/usr/bin/gparted"
        else:
            self.ext_partitioner = "nopartitioner"

        # global periodic timer/counter
        self.numticks = 0

        # current/previous wizard page/mode state
        self.current_mode = "intro"
        self.last_mode = "intro"

        # used by periodic function to check for the external 
        # partitioner having terminated
        self.waiting_on_partitioner = False

        # the goods: the user choices for rebootless live installation options
        self.rps_choice = "none"
        self.bps_choice = "none"
        self.sps_choice = "none"

        ## 
        ## add a timeout handler to run periodic function
        ##
        self.timeout_handler_id = gobject.timeout_add(POLL_INTERVAL, 
                                                      self.do_periodic)

        # set initial mode
        self.set_mode("intro")

        # show the GUI to the user
        # note: seems better to explicitly decide when to show the GUI
        self.main_window.show()

        # work around problems seen on f10 derivative, perhaps related
        # to zenity's inspirational problem.  I.e. window starting up
        # underneath others that are not keep_above.
        time.sleep(1.23)
        self.main_window.present()

    # run main GTK GUI infinite event processing loop
    def handle_gui_events(self):
        # edunote: faq.pygtk.org suggests that this being in the main
        # edunote: thread, and it needn't be wrapped with threads_enter
        # edunote: and threads_leave, despite the fact that I ran across
        # edunote: some random code on the net that did that.
        gtk.main()


    # change wizard page to new mode
    def set_mode(self, newmode):
        # set last_mode
        self.last_mode = self.current_mode

        # disconnect all treestore from all treeviews
        self.rps_choices.set_model()
        self.bps_choices.set_model()
        self.sps_choices.set_model()

        # clear all entries in the treestore
        for choice in self.dest_vol_choices_iters.values():
            self.dest_vol_choices_treestore.remove(choice)

        # note: this method seems not to work
        #
        # treeiter = self.dest_vol_choices_treestore.get_iter_first()
        # while treeiter:
        #     nextiter = self.dest_vol_choices_treestore.iter_next(treeiter)
        #     self.dest_vol_choices_treestore.remove(treeiter)
        #     treeiter = nextiter
        #
        # note: this seemed like a segfaultingly bad alternative as well
        #
        # self.dest_vol_choices_treestore.clear()

        # all the iters have been removed 
        # TODO: figure out some way to double check, raising exception
        self.dest_vol_choices_iters = {}

        #
        # flip gui main notebook page
        #
        self.main_notebook.set_current_page(MODES[newmode])

        #
        # run per mode custom initialization (post pageflip)
        #

        # generate list of choices to present user
        if (newmode == "rps"):
            # connect the treestore to the rps treeview widget
            self.rps_choices.set_model(self.dest_vol_choices_treestore)
            # exit this func immediately, i.e. spawn worker thread to
            # do this after mode change so user doesn't see hung UI
            self.init_rps_vol_choices_thread = \
                threading.Thread(target=self.init_rps_vol_choices)
            self.init_rps_vol_choices_thread.start()
        elif (newmode == "bps"):
            # connect the treestore to the bps treeview widget
            self.bps_choices.set_model(self.dest_vol_choices_treestore)
            # no need for threadsafe_ wrapper, because this is the main thread
            self.gen_vol_choices(newmode)
        elif (newmode == "sps"):
            # connect the treestore to the sps treeview widget
            self.sps_choices.set_model(self.dest_vol_choices_treestore)
            # no need for threadsafe_ wrapper, because this is the main thread
            self.gen_vol_choices(newmode)

        # set current_mode
        self.current_mode = newmode

    # initialize the data structures related to user choices of storage
    # volumes
    def init_dest_vol_stuff(self):
        """Create treestoremodel for *_choices and attach to the 
        *_choices widgets.

        """

        # the iters are stored in a hash keyed by shortname, in order
        # to be able to remove them later 
        # (treestore.clear() seems to cause serious pygtk bug/segfault)
        # TODO: add some raise exception if flag testing shows iters are 
        #       not persistent
        self.dest_vol_choices_iters = {}

        # initialize dest_vol_choices until scan_volumes does it better
        self.dest_vol_choices = []

        # note: here we set up for 4 columns of strings
        self.dest_vol_choices_treestore = gtk.TreeStore(gobject.TYPE_STRING, 
                                                        gobject.TYPE_STRING,
                                                        gobject.TYPE_STRING,
                                                        gobject.TYPE_STRING)


        # get selection objects, and attach event handlers
        self.rps_choices_selection = \
            self.rps_choices.get_selection()
        self.rps_choices_selection.connect( \
            'changed', self.on_rps_choices_selection_changed)
        self.bps_choices_selection = \
            self.bps_choices.get_selection()
        self.bps_choices_selection.connect( \
            'changed', self.on_bps_choices_selection_changed)
        self.sps_choices_selection = \
            self.sps_choices.get_selection()
        self.sps_choices_selection.connect( \
            'changed', self.on_sps_choices_selection_changed)


        # XXX: there has to be a better way to clean up below seeming code 
        #      repitition but for now, there should never be a scale up 
        #      from N=3 selectionscreens.  Could use copy(x) (or try 
        #      deepcopy(x))of the column objects perhaps.

        ###
        ### main column
        ###

        # for rps
        main_column_renderer = gtk.CellRendererText()
        main_column = \
            gtk.TreeViewColumn("Storage Volume Options", 
                               main_column_renderer,
                               markup=0)
        # only the main column is expand = True
        main_column.set_expand(True)
        self.rps_choices.append_column(main_column)

        # for bps
        main_column_renderer = gtk.CellRendererText()
        main_column = \
            gtk.TreeViewColumn("Storage Volume Options", 
                               main_column_renderer,
                               markup=0)
        main_column.set_expand(True)
        self.bps_choices.append_column(main_column)

        # for sps
        main_column_renderer = gtk.CellRendererText()
        main_column = \
            gtk.TreeViewColumn("Storage Volume Options", 
                               main_column_renderer,
                               markup=0)
        main_column.set_expand(True)
        self.sps_choices.append_column(main_column)


        ###
        ### shortname column
        ###

        # shortname column: e.g. 'sda1'

        # for rps
        shortname_column_renderer = gtk.CellRendererText()
        shortname_column = gtk.TreeViewColumn("Short", 
                                                  shortname_column_renderer, 
                                                  markup=1)
        shortname_column.set_expand(False)
        self.rps_choices.append_column(shortname_column)

        # for bps
        shortname_column_renderer = gtk.CellRendererText()
        shortname_column = gtk.TreeViewColumn("Short", 
                                                  shortname_column_renderer, 
                                                  markup=1)
        shortname_column.set_expand(False)
        self.bps_choices.append_column(shortname_column)

        # for sps
        shortname_column_renderer = gtk.CellRendererText()
        shortname_column = gtk.TreeViewColumn("Short", 
                                                  shortname_column_renderer, 
                                                  markup=1)
        shortname_column.set_expand(False)
        self.sps_choices.append_column(shortname_column)


        ##
        ## size column
        ##

        # size column: size of destination volume option

        # for rps
        size_column_renderer = gtk.CellRendererText()

        # this works ...
        #size_column_renderer.set_property('foreground', 'red')
        #
        # ... so why doesn't this?
        # (see unanswered plea - 
        # http://www.python-forum.org/pythonforum/viewtopic.php?f=4&t=2151)
        size_column_renderer.set_property('alignment', pango.ALIGN_RIGHT)
        # ... which is why I'm using this annoying workaround 
        # (see db_size return formatting too)
        # (i.e. the goal here is simple right justification)
        size_column_renderer.set_property('family', 'Monospace')

        # set up the Size column
        size_column = gtk.TreeViewColumn("Size(GB)", 
                                         size_column_renderer, 
                                         markup=2)

        # this right justifies only the column header, not the column data
        size_column.set_alignment(1.0)

        size_column.set_expand(False)

        self.rps_choices.append_column(size_column)


        # for bps
        size_column_renderer = gtk.CellRendererText()
        size_column_renderer.set_property('alignment', pango.ALIGN_RIGHT)
        size_column_renderer.set_property('family', 'Monospace')
        size_column = gtk.TreeViewColumn("Size(GB)", 
                                         size_column_renderer, 
                                         markup=2)
        size_column.set_alignment(1.0)
        size_column.set_expand(False)
        self.bps_choices.append_column(size_column)


        # for sps
        size_column_renderer = gtk.CellRendererText()
        size_column_renderer.set_property('alignment', pango.ALIGN_RIGHT)
        size_column_renderer.set_property('family', 'Monospace')
        size_column = gtk.TreeViewColumn("Size(GB)", 
                                         size_column_renderer, 
                                         markup=2)
        size_column.set_alignment(1.0)
        size_column.set_expand(False)
        self.sps_choices.append_column(size_column)


        ##
        ## type column
        ##

        # type column: currenttype of destination volume option

        # for rps
        type_column_renderer = gtk.CellRendererText()
        type_column = gtk.TreeViewColumn("Type", 
                                             type_column_renderer, 
                                             markup=3)
        type_column.set_expand(False)
        self.rps_choices.append_column(type_column)

        # for bps
        type_column_renderer = gtk.CellRendererText()
        type_column = gtk.TreeViewColumn("Type", 
                                             type_column_renderer, 
                                             markup=3)
        type_column.set_expand(False)
        self.bps_choices.append_column(type_column)

        # for sps
        type_column_renderer = gtk.CellRendererText()
        type_column = gtk.TreeViewColumn("Type", 
                                             type_column_renderer, 
                                             markup=3)
        type_column.set_expand(False)
        self.sps_choices.append_column(type_column)

        ##
        ## exclude root choice from boot selection
        ##
        self.bps_choices_selection.set_select_function( \
            self.bps_choices_selection_func)

        ##
        ## exclude root and boot choices from swap selection
        ##
        self.sps_choices_selection.set_select_function( \
            self.sps_choices_selection_func)

    # this function checks a potentially selectable item, and disallows 
    # it if it matches the rps or bps choice
    def bps_choices_selection_func(self, info):
        # get the item's path
        (path_to_test,) = info
        # get the item's iter from the path
        iter_to_test = self.dest_vol_choices_treestore.get_iter(path_to_test)
        # get the value from the first column of the item
        short_to_test = \
            self.dest_vol_choices_treestore.get_value(iter_to_test, 0)
        # remove markup
        short_to_test = remove_markup(short_to_test)
        # compare against lvm which /boot cannot yet live on
        if (self.dest_vol_choices_longnames[short_to_test].startswith("/dev/mapper")):
            return False
        # compare against rps choice
        if self.must_have_seperate_boot is False:
            return True
        else:
            if (self.dest_vol_choices_longnames[short_to_test] == self.rps_choice):
                return False
            else:
                return True

    # this function checks a potentially selectable item, and disallows 
    # it if it matches the rps or bps choice
    def sps_choices_selection_func(self, info):
        # get the item's path
        (path_to_test,) = info
        # get the item's iter from the path
        iter_to_test = self.dest_vol_choices_treestore.get_iter(path_to_test)
        # get the value from the first column of the item
        short_to_test = \
            self.dest_vol_choices_treestore.get_value(iter_to_test, 0)
        short_to_test = remove_markup(short_to_test)
        # compare against rps and bps choices
        if (self.dest_vol_choices_longnames[short_to_test] == \
                self.rps_choice) or \
                (self.dest_vol_choices_longnames[short_to_test] == \
                     self.bps_choice):
            return False
        else:
            return True


    #########################################################################
    #########################################################################
    ##
    ## GUI event signal handlers
    ##
    #########################################################################
    #########################################################################


    def on_logo_size_allocate(self, widget, allocation):
        # This took me a couple days to figure out.  Perhaps it was
        # all really just the container size_requests, and doing this
        # in main_window configure event handler would work as well.

        # reviewer: "gtk.Image has no attribute visible"???  
        # note: this was an attempt to only futz with the currently shown logo
        #        if self.intro_logo.visible is not True:
        #        if widget.visible is not True:
        #            return False

        # only bother with image resizing of the allocated dimensions
        # of the gtk.Image widget have changed.
        if ((allocation.height != self.logo_old_allocation_height) or
            (allocation.width != self.logo_old_allocation_width)):

            # maintain aspect ratio
            new_aspect_ratio = allocation.width / allocation.height
            if (new_aspect_ratio > self.gpb_aspect_ratio):
                new_logo_height = allocation.height
                new_logo_width = new_logo_height * self.gpb_aspect_ratio
            else:
                new_logo_width = allocation.width
                new_logo_height = allocation.width / self.gpb_aspect_ratio
                
            # scale the logo to the new appropriate/calculated dimensions
            self.ngpb = self.gpb.scale_simple(int(new_logo_width),
                                              int(new_logo_height),
                                              gtk.gdk.INTERP_BILINEAR)

            # TODO: replace this with a better mechanism.  See above.
            #       Until figuring out that solution, maybe indulge in
            #       an eval for loop here, and elsewhere.
            self.error_logo.set_from_pixbuf(self.ngpb)
            self.intro_logo.set_from_pixbuf(self.ngpb)
            self.partitioner_logo.set_from_pixbuf(self.ngpb)
            self.rps_logo.set_from_pixbuf(self.ngpb)
            self.bps_logo.set_from_pixbuf(self.ngpb)
            self.sps_logo.set_from_pixbuf(self.ngpb)
            self.review_logo.set_from_pixbuf(self.ngpb)
            self.installing_logo.set_from_pixbuf(self.ngpb)
            self.success_logo.set_from_pixbuf(self.ngpb)

            # done
            self.logo_old_allocation_width = allocation.width
            self.logo_old_allocation_height = allocation.height

        # TODO: document what this means (forgot and don't care already)
        return False


    # function to handle window resize events (and first size initialization)
    def on_main_window_configure_event(self, widget, event):
        return False
        
    def on_main_window_destroy(self, widget):
        # nice, but not necessary
        # gtk.main_quit()
        sys.exit(0)

    def on_error_button_exit_clicked(self, widget):
        sys.exit(0)

    def on_intro_button_exit_clicked(self, widget):
        sys.exit(0)

    # TODO: maybe this becomes DeviceKit at some point?
    def launch_partitioner(self):
        arglist = [self.ext_partitioner]

        # supress gparted telling us about kernel unable to
        # reread part table.  
        # TODO: use fdisk -l vs blockdev output to detect that
        #       situation and handle as best as possible
        dev_null = os.open("/dev/null", os.O_WRONLY)
        try:
            ext_part_proc = subprocess.Popen(arglist,
                                             stdout=dev_null,
                                             stderr=dev_null)
            ext_part_proc.wait()
        finally:
            os.close(dev_null)


        # move on
        # edunote: could also put the mode change in the main
        # edunote: thread, polling a global flag set here.  That
        # edunote: technique is used for the installation progress
        # edunote: bar, but this will stay, for the bonus educational
        # edunote: value.
        gtk.gdk.threads_enter()
        try:
            # note: could just do "intro" instead of last_mode
            self.set_mode(self.last_mode)
        finally:
            gtk.gdk.threads_leave()


    def on_intro_button_partitioner_clicked(self, widget):
        # create a thread for seperate partitioner utility
        if (self.ext_partitioner == "nopartitioner"):
            raise ZyXLiveInstallerGUIError( \
                self, 
                "neither palimsest nor gparted external partitioners are" +
                " available.  Advanced users are welcome to try fdisk" +
                " from the commandline and restart zyx-liveinstaller.")
        else:
            self.partitioner_thread = \
                threading.Thread(target=self.launch_partitioner)
            self.set_mode("partitioner")
            # let the thread run
            self.partitioner_thread.start()
            # perhaps pointless watchdog facility
            self.waiting_on_partitioner = True
        

    def on_intro_button_next_clicked(self, widget):
        # exit if not a running LiveOS and not a developer tree
        if not os.path.exists("/.liveimg-configured"):
#            if not DEVELOPER_DEBUG:
            if not _developer_tree:
                raise ZyXLiveInstallerGUIError( \
                    self, 
                    "This does not appear to be a running LiveOS.  The file" +
                    " /.liveimg-configured does not exist")
        # initially, user can't hit next on rps or bps until they choose a 
        # volume
        self.rps_button_next.set_sensitive(False)
        self.bps_button_next.set_sensitive(False)
        # ???: an attempt to unselect everything.  Either of the below
        #      two methods leave the previously selected item highlighted.
        #      As a result, I just went with an extra invalid selection at 
        #      the top, doubling as a header.
        # note: that the new method of removing all treestore entrys/iters 
        #       on every mode change, results in nothing selected by default
#        self.rps_choices_selection.unselect_all()
#        self.rps_choices_selection.unselect_iter(self.top_iter)
        self.set_mode("rps")

    def on_partitioner_button_exit_clicked(self, widget):
        sys.exit(0)

    def on_partitioner_button_abort_clicked(self, widget):
        # TODO: notimplementedyet (send kill signal to gparted)
        sys.exit(0)

    def on_rps_button_exit_clicked(self, widget):
        sys.exit(0)

    def on_rps_button_back_clicked(self, widget):
        self.set_mode("intro")

    def on_rps_choices_selection_changed(self, widget):
        # get the appropriate selection object
        selection = self.rps_choices.get_selection()
        
        # first easiest check is that a row is selected
        if (selection.count_selected_rows() == 0):
            self.rps_button_next.set_sensitive(False)
            return

        # now make sure it isn't the top row, because for rps, 
        # a choice is mandatory
        (selected_treemodel, selected_treeiter) = selection.get_selected()
        if selected_treeiter is not None:
            selected_first_column_value = \
                selected_treemodel.get_value(selected_treeiter, 0)
            selected_second_column_value = \
                selected_treemodel.get_value(selected_treeiter, 1)
            if (selected_first_column_value.find( \
                    "Select one of the following") != -1):
                # disable the next button widget until a valid selection 
                # is available
                self.rps_button_next.set_sensitive(False)
            else:
                # record the valid current selection and ...
                self.rps_choice = \
                    self.dest_vol_choices_longnames[\
                    selected_first_column_value]
                # ... allow the user to move on
                self.rps_button_next.set_sensitive(True)
                # and if seperate /boot is not required, make it default
                # to the root choice (but only if rps is non lvm)
                if self.must_have_seperate_boot is False:
                    if not self.rps_choice.startswith("/dev/mapper"):
                        self.bps_choice = self.rps_choice
                        self.bps_button_next.set_sensitive(True)

    def on_rps_button_next_clicked(self, widget):
        self.unmount_if_needed(self.rps_choice)
        self.set_mode("bps")

    def on_bps_button_exit_clicked(self, widget):
        sys.exit(0)

    def on_bps_button_back_clicked(self, widget):
        self.set_mode("rps")

    def on_bps_choices_selection_changed(self, widget):
        # see similar rps function

        # get the appropriate selection object
        selection = self.bps_choices.get_selection()
        
        # first easiest check is that a row is selected
        if (selection.count_selected_rows() == 0):
            self.bps_button_next.set_sensitive(False)
            return

        # now make sure it isn't the top row, because for bps, 
        # a choice is mandatory
        (selected_treemodel, selected_treeiter) = selection.get_selected()
        # perhaps this and similar checks for None are pointless as above
        # already exits this function if there are no selected rows.  But
        # I added these checks while fighting a segfault dealing with 
        # the apparent use of an invalid iter
        if selected_treeiter is not None:
            selected_first_column_value = \
                selected_treemodel.get_value(selected_treeiter, 0)
            selected_second_column_value = \
                selected_treemodel.get_value(selected_treeiter, 1)
            if (selected_first_column_value.find( \
                    "Select one of the following") != -1):
                # disable the next button widget until a valid selection 
                # is available
                self.bps_button_next.set_sensitive(False)
            else:
                # record the valid current selection and ...
                self.bps_choice = \
                    self.dest_vol_choices_longnames[\
                        remove_markup(selected_first_column_value)]
                # ... allow the user to move on
                self.bps_button_next.set_sensitive(True)

    def on_bps_button_next_clicked(self, widget):
        self.unmount_if_needed(self.bps_choice)
        self.set_mode("sps")

    def on_sps_button_exit_clicked(self, widget):
        sys.exit(0)

    def on_sps_button_back_clicked(self, widget):
        self.set_mode("bps")

    def on_sps_choices_selection_changed(self, widget):
        # see similar rps/bps functions
        selection = self.sps_choices.get_selection()
        
        (selected_treemodel, selected_treeiter) = selection.get_selected()
        if selected_treeiter is not None:
            selected_first_column_value = \
                selected_treemodel.get_value(selected_treeiter, 0)
            selected_second_column_value = \
                selected_treemodel.get_value(selected_treeiter, 1)
            self.sps_choice = \
                self.dest_vol_choices_longnames[selected_first_column_value]
            if (self.sps_choice == ""):
                self.sps_choice = "none"
        
    def on_sps_button_next_clicked(self, widget):

        self.unmount_if_needed(self.bps_choice)

        #
        # prepare review and installing text widget text
        #

        # swap is optional, so its part in this text is as well
        if (self.sps_choice == "none"):
            opt_swap_text_first = ""
            opt_swap_text_second = ""
        else:

            opt_swap_text_first = \
"""WARNING: about to WIPE and format swap on storage volume
%(swap_name)s
""" % { 'swap_name' : os.path.basename(self.sps_choice), }

            opt_swap_text_second = \
"""Swap Storage Volume Choice:
%(swap_long)s
will have all data WIPED, then be used for this LiveOS installation (swap).

""" % { 'swap_long' : self.sps_choice, }
        

        # note: possibly excessive attempt to maintain 79 character code width
        self.set_review_text( \
("""WARNING: about to WIPE and install root filesystem on storage volume 
%(root_name)s

WARNING: about to WIPE and install boot filesystem on storage volume
%(boot_name)s

%(opt_swap_text_first)s
WARNING WARNING WARNING -- This is your final warning before beginning""" + \
""" a 'destructive' installation of the running LiveOS.  All existing""" + \
""" data on the following volumes will be be lost during installation.""" + \
"""  If you require an installation that preserves data on the""" + \
""" destination volumes, use the traditional Anaconda installer.

Root Storage Volume Choice:
 %(root_long)s 
will have all data WIPED, then be used for this LiveOS installation""" + \
""" (root-'/').

Boot Storage Volume Choice:
 %(boot_long)s
will have all data WIPED, then be used for this LiveOS installation""" + \
""" (boot-'/boot').

%(opt_swap_text_second)s
Click 'next' to proceed with installation, or 'back' to change target""" + \
""" volume selections, or 'exit' to close this installer without""" + \
""" installing.
""") % { 'root_name' : os.path.basename(self.rps_choice),
         'boot_name' : os.path.basename(self.bps_choice),
         'root_long' : self.rps_choice,
         'boot_long' : self.bps_choice,
         'opt_swap_text_first' : opt_swap_text_first,
         'opt_swap_text_second' : opt_swap_text_second,
         })


        self.set_installing_text( \
            ("Installation is in progress to the following" + \
                 " partitions/volumes:\n\n" + \
                 "root filesystem ::\n%(rchoice)s\n\n" + \
                 "boot filesystem ::\n%(bchoice)s\n\n" + \
                 "swap space      ::\n%(schoice)s\n\n" + \
                 "\n" + self.install_text + \
                 "") % { 'rchoice' : self.rps_choice,
                         'bchoice' : self.bps_choice,
                         'schoice' : self.sps_choice,
                         })

        self.set_mode("review")

    def on_review_button_exit_clicked(self, widget):
        sys.exit(0)

    def on_review_button_back_clicked(self, widget):
        self.set_mode("sps")

    def on_review_button_next_clicked(self, widget):
        # create installer thread
        self.installer_thread = threading.Thread(target=self.run_installer)
        # start installer thread
        self.installer_thread.start()
        # change GUI mode
        self.set_mode("installing")

    def on_installing_button_abort_exit_clicked(self, widget):
        # todo: are-you-sure mechanism (too easy to abort)
        # note: this may be a race condition, perhaps create installer 
        #       object when self/guiinstaller is being initialized (but 
        #       pretty unlikely)
        self.installer.request_installation_abort()
        # FIXME: need mech to wait on abort, not just request
        sys.exit(0)

    def on_installing_button_abort_back_clicked(self, widget):
        self.installer.request_installation_abort()
        # reset the GUI state for the installer, for now, just this
        self.installing_progressbar.set_fraction(0.0)
        # return to the previous installation wizard page
        self.set_mode("review")

    def on_success_button_viewdocs_clicked(self, widget):
        # notyetimplemented
        sys.exit(0)

    def on_success_button_done_clicked(self, widget):
        # done
        sys.exit(0)


    #########################################################################
    #########################################################################
    ##
    ## non event handling functions (called by event signal handlers)
    ##
    #########################################################################
    #########################################################################

    # set the text in the error mode/page
    def set_error_text(self, new_text):
        (self.error_text.get_buffer()).set_text(new_text)

    # set the text in the final review mode/page
    def set_review_text(self, new_text):
        (self.review_text.get_buffer()).set_text(new_text)

    # set the text in the installation mode/page
    def set_installing_text(self, new_text):
        (self.installing_text.get_buffer()).set_text(new_text)

    def run_installer(self):
        self.installer.root_device = self.rps_choice
        self.installer.boot_device = self.bps_choice
        self.installer.swap_device = self.sps_choice
        try:
            self.installer.do_install()
        except rli.ZyXLiveInstallerError, e:
            raise ZyXLiveInstallerGUIError( \
                self, 
                "*INSTALLER BACKEND ERROR*\n\nIf possible, please " +
                "send the file\n\n/var/log/zyx-liveinstaller.log\n\nto\n\nbugs AT " +
                "viros DOT org\n\n--\n\n" + str(e) )

    # pre-rps initialization of all volume choices infrastructure
    # (that which can be done prior to volume scan)
    def init_vol_choices(self):
        # ... to populate volume/partition choices widget(s)
        self.dest_vol_choices_treestore.clear()

        # this adds the first fake entry
        self.top_iter = self.dest_vol_choices_treestore.append(None)
        self.dest_vol_choices_treestore.set_value(self.top_iter, 
                                                  0, 
 '<span size="large">Scanning storage volumes, please wait a few ' + \
 'seconds...</span>')
        self.dest_vol_choices_treestore.set_value(self.top_iter, 
                                                  1, 
                                                  "")
        self.dest_vol_choices_treestore.set_value(self.top_iter, 
                                                  2, 
                                                  "")
        self.dest_vol_choices_treestore.set_value(self.top_iter, 
                                                  3, 
                                                  "")
    def gen_vol_choices(self, mode):
        # craft header string appropriate to mode
        if (mode == "rps"):
            header_string = \
                '<span size="large">Select one of the following -</span>'
        elif (mode == "bps"):
            # when bootloader handles ext4, this becomes optional or gone
            header_string = \
                '<span size="large">Select one of the following -</span>'
        elif (mode == "sps"):
            header_string = \
                '<span size="large" foreground="#007700"><u>Optionally' + \
                '</u></span><span size="large"> select one of the' + \
                ' following -</span>'
        else:
            raise ZyXLiveInstallerGUIError( \
                self, 
                "unknown mode ... %s ..." % mode)

        # 
        # craft header entry/iter
        # 
        self.dest_vol_choices_treestore.set_value(self.top_iter, 
                                                  0, 
                                                  header_string)
        self.dest_vol_choices_treestore.set_value(self.top_iter, 
                                                  1, 
                                                  "")
        self.dest_vol_choices_treestore.set_value(self.top_iter, 
                                                  2, 
                                                  "")
        self.dest_vol_choices_treestore.set_value(self.top_iter, 
                                                  3, 
                                                  "")
                    
        # a hash of the longnames keyed by short will be needed to
        # unmangle the text when the user goes backward through the wizard
        self.dest_vol_choices_longnames = {}
            
        for target_vol in self.dest_vol_choices:
            # get the shortname from the longname
            target_vol_shortname = os.path.basename(target_vol)
            # create an iter for this potential choice
            self.dest_vol_choices_iters[target_vol_shortname] = \
                self.dest_vol_choices_treestore.append(None)

            # populate the shortname->longname hash
            # NOTE: implicit assumption you won't see non identical 
            #       duplicates between /dev/disk/by-id and /dev/mapper
            self.dest_vol_choices_longnames[target_vol_shortname] = \
                target_vol

            #
            # craft the main and type column string values,
            # 

            # fist, set the default values
            main_column_string = target_vol_shortname
            type_column_string = get_device_partition_type(target_vol)

            # first, check to see if it needs to be 'new root'
            if ((mode is "bps") or (mode is "sps")):
                # edunote: can't use 'is' instead of == for strings
                if (target_vol == self.rps_choice):
                    main_column_string = \
                        '<span foreground="#FF0000">%s</span>' % \
                        target_vol_shortname
                    type_column_string = \
                        '<span foreground="#FF0000">new root</span>'
                    
            # second, check to see if it needs to be 'new boot'
            if (mode == "sps"):
                if (target_vol == self.bps_choice):
                    main_column_string = \
                        '<span foreground="#FF0000">%s</span>' % \
                        target_vol_shortname
                    type_column_string = \
                        '<span foreground="#FF0000">new boot</span>'
                    
            # set the values for each column for this choice
            self.dest_vol_choices_treestore.set_value( \
                self.dest_vol_choices_iters[target_vol_shortname],
                0, 
                main_column_string)
            self.dest_vol_choices_treestore.set_value( \
                self.dest_vol_choices_iters[target_vol_shortname],
                1, 
                get_device_realshortname(target_vol))
            self.dest_vol_choices_treestore.set_value( \
                self.dest_vol_choices_iters[target_vol_shortname],
                2, 
                blockdev_size(target_vol))
            self.dest_vol_choices_treestore.set_value( \
                self.dest_vol_choices_iters[target_vol_shortname],
                3, 
                type_column_string)

            # if an entry was previously selected, have it be the 
            # default selection
            if (mode == "rps"):
                if (os.path.basename(self.rps_choice) == target_vol_shortname):
                    self.rps_choices_selection.select_iter( \
                        self.dest_vol_choices_iters[target_vol_shortname])
            elif (mode == "bps"):
                if (os.path.basename(self.bps_choice) == target_vol_shortname):
                    self.bps_choices_selection.select_iter( \
                        self.dest_vol_choices_iters[target_vol_shortname])
            elif (mode == "sps"):
                if (os.path.basename(self.sps_choice) == target_vol_shortname):
                    self.sps_choices_selection.select_iter( \
                        self.dest_vol_choices_iters[target_vol_shortname])
        
    def threadsafe_gen_vol_choices(self, mode):
        # reviewer: Is this wrapping necessary/appropriate?  
        #           This is 'directly' effecting the GUI
        gtk.gdk.threads_enter()
        try:
            self.gen_vol_choices(mode)
        finally:
            gtk.gdk.threads_leave()

    def init_rps_vol_choices(self):
        # pre volume scan initialization
        gtk.gdk.threads_enter()
        try:
            self.init_vol_choices()
        finally:
            gtk.gdk.threads_leave()

        # disk device scan ...
        self.scan_volumes()

        # post volume scan initialization
        self.threadsafe_gen_vol_choices("rps")


    # this could be moved to a utility function outside the class
    # (DeviceKit/pyparted perhaps)
    def scan_volumes(self):
        unfiltered_choices_list = []
        if os.path.exists("/dev/mapper"):
            for entry in os.listdir("/dev/mapper"):
                unfiltered_choices_list.append("/dev/mapper/" + entry)
        if os.path.exists("/dev/disk/by-id"):
            for entry in os.listdir("/dev/disk/by-id"):
                unfiltered_choices_list.append("/dev/disk/by-id/" + entry)
#        unfiltered_choices_list.sort()
        self.dest_vol_choices = []
        for candidate_vol in unfiltered_choices_list:
            keep = True
            # ignore f11 style LiveOS devicemapper volumes
            if (candidate_vol.startswith("/dev/disk/by-id/dm-name-live-") or
                candidate_vol.startswith("/dev/mapper/live-") or
                candidate_vol.startswith(\
                    "/dev/disk/by-id/dm-name-zyx-liveos-") or
                candidate_vol.startswith("/dev/mapper/zyx-liveos-") or
                candidate_vol.startswith("/dev/mapper/control")):
                keep = False
            else:
                for target_vol in self.dest_vol_choices:
                    #
                    # don't keep if already in dest_vol_choices (not unique)
                    #

                    # first check symlink equivalence
                    if (os.path.realpath(candidate_vol) == 
                        os.path.realpath(target_vol)):
                        keep = False
                        
                    # finally check for equivalent device nodes
                    candidate_vol_major = \
                        os.major(\
                        os.stat(os.path.realpath(candidate_vol)).st_rdev)
                    candidate_vol_minor = \
                        os.minor(\
                        os.stat(os.path.realpath(candidate_vol)).st_rdev)
                    target_vol_major = \
                        os.major(\
                        os.stat(os.path.realpath(target_vol)).st_rdev)
                    target_vol_minor = \
                        os.minor(os.stat(os.path.realpath(target_vol)).st_rdev)
                    if ((candidate_vol_major == target_vol_major) and
                        (candidate_vol_minor == target_vol_minor)):
                        keep = False

            # keep the entry if it is unique
            if keep:
                self.dest_vol_choices.append(candidate_vol)

        self.dest_vol_choices.sort()


    # if the given device is mounted under /media and unused, unmount it,
    # otherwise, raise an exception.
    def unmount_if_needed(self, device):
        # check procselfmountinfo against maj/min, then look at /media, 
        # then try to unmount
        device_major = \
            os.major(os.stat(os.path.realpath(device)).st_rdev)
        device_minor = \
            os.minor(os.stat(os.path.realpath(device)).st_rdev)

        if os.path.exists("/proc/self/mountinfo"):
            mountinfo = open("/proc/self/mountinfo", "r")
            have_mountinfo = True
        elif os.path.exists("/proc/self/mounts"):
            mountinfo = open("/proc/self/mounts", "r")
            have_mountinfo = False
        else:
            raise ZyXLiveInstallerGUIError( \
                self, 
                "no /proc/self/mountinfo OR /proc/self/mounts")

        
        for mount in mountinfo.readlines():
            if have_mountinfo is True:
                mount_major = int(mount.split()[2].split(":")[0])
                mount_minor = int(mount.split()[2].split(":")[1])
                mount_point = mount.split()[4]
            else:
                if os.path.exists(mount.split()[0]) is True:
                    mount_major = os.major( \
                        os.stat(os.path.realpath(mount.split()[0])).st_rdev)   
                    mount_minor = os.minor( \
                        os.stat(os.path.realpath(mount.split()[0])).st_rdev)   
                else:
                    mount_major = -1
                    mount_minor = -1

                mount_point = mount.split()[1]
                    

            if ((device_major == mount_major) and
                (device_minor == mount_minor)):

                # /mnt/disc(lvm)/ is centos-5.4's version of /media for nonremovable discs
                if mount_point.startswith("/media/") or \
                        mount_point.startswith("/mnt/disc/") or \
                        mount_point.startswith("/mnt/lvm/"):
                    # mount_point is /media/*, try to unmount if possible

                    dev_null = os.open("/dev/null", os.O_WRONLY)
                    try:
                        fuser_proc = subprocess.Popen(["/sbin/fuser", 
                                                        "-m",
                                                        mount_point],
                                                       stdout=subprocess.PIPE,
                                                       stderr=dev_null)
                        fuser_out = fuser_proc.communicate()[0]
                    finally:
                        os.close(dev_null)
        
                    # check the return value of fuser -m /media/point
                    if fuser_proc.returncode:
                        # nobody using the mount, try to unmount it
                        dev_null = os.open("/dev/null", os.O_WRONLY)
                        try:
                            umount_proc = \
                                subprocess.Popen(["/bin/umount", 
                                                  mount_point], 
                                                 stdout=subprocess.PIPE,
                                                 stderr=dev_null)
                            umount_out = umount_proc.communicate()[0]
                        finally:
                            os.close(dev_null)

                        if umount_proc.returncode:
                            # umount failed, raise exception
                            raise ZyXLiveInstallerGUIError( \
                                self, 
                                ("the volume you selected - %s - is " +
                                 "currently mounted as %s, and cannot be " +
                                 "unmounted.") % (device, mount_point))
                        
                        else:
                            # umount succeeded, done
                            return True
                            
                        
                        True
                    else:
                        # some process(es) using the mount, exception
                        raise ZyXLiveInstallerGUIError( \
                            self, 
                            ("the volume you selected - %s - is currently " +
                             "mounted as %s, and cannot be unmounted because" +
                             "it is in use by these processes - %s") %
                            (device, mount_point, fuser_out))
                else:
                    # mount_point is not /media/*, raise exception
                    raise ZyXLiveInstallerGUIError( \
                        self, 
                        ("the volume you selected - %s - is currently " +
                         "mounted as %s") % (device, mount_point))

        return True

    ##
    ## periodic/timer function(s)
    ##

    def do_periodic(self):
        # not actually using timekeeping at the moment
#        self.numticks = self.numticks + 1

        #
        # handle being idle during external partitioner mode
        #
        # this should not strictly be necessary, and may be removed
        # (as the thread itself changes mode right before exiting)
        if self.waiting_on_partitioner is True:
            # in case (?) the thread exploded before exiting 
            if self.partitioner_thread.isAlive() is False:
                if (self.current_mode != "intro"):
                    self.set_mode("intro")
                self.waiting_on_partitioner = False
 
        #
        # handle being idle during external installation in progress mode
        #
        if (self.current_mode == "installing"):
            # check to see if the installer thread completed
            if self.installer_thread.isAlive() is not True:
                self.set_mode("success")
                
            # note: this is the main thread, presuming it is ok to not
            #       wrap in gtk.gdk.threads_enter/leave()
            # edunote: set_fraction seems broken, setting with 1.000000 seemed
            # edunote: to trigger assertion on 0.0 <= set_percentage(?) <= 1.0
            if (self.installer.progress >= 1.0):
                # edunote: WTF?: this hits when/if 
                # edunote: self.installer.progress == 1.00000
                # edunote: Answer seems to be float precision, i.e. 
                # edunote: 1.0 != 1.000000 (?)
                raise ZyXLiveInstallerGUIError( \
                    self, 
                    "progress 'greater' than 1.0 -- %f" \
                        % self.installer.progress)
            else:
                self.installing_progressbar.set_fraction( \
                    self.installer.progress)
        
        # return true so the function will be called again next period
        return True

#############################################################################
#############################################################################
##
## utility functions
##
## TODO: at least these can be moved to a different source file
##
#############################################################################
#############################################################################


def remove_markup(string):
    """Remove <> style markup from a string.

    string -- a string possibly containing <> style markups

    """
    result=""
    markup_depth=0
    for char in list(string):
        if char is '<':
            markup_depth = markup_depth + 1
        elif char is '>':
            markup_depth = markup_depth - 1
        elif (markup_depth == 0):
            result = result + char

    return result


def blockdev_size(block_device):
    """Input a block device and output its size in GB.

    block_device -- a block device given by its path, e.g. /dev/sda1

    """
       
    dev_null = os.open("/dev/null", os.O_WRONLY)
    try:
        helper_proc = subprocess.Popen(["/sbin/blockdev", 
                                        "--getsize64",
                                        block_device],
                                       stdout=subprocess.PIPE,
                                       stderr=dev_null)
        helper_out = helper_proc.communicate()[0]
    finally:
        os.close(dev_null)
        
    # note: I had this above the helper_out= code, and I'd never see
    #       the clause hit, i.e. when not run as root.  My best 
    #       understanding thus far is that the process does not really
    #       launch until the .communicate()[0] is called ??
    if helper_proc.returncode:
        return "n/a"
    else:
 
        try:
            # web has copyrighted 'your first python program' examples of 
            # the full monty
            bd_answer = str(int(helper_out.split()[0]) / 1024 / 1024 / 1024)
        except:
            bd_answer = "n/a"

        if (bd_answer == "n/a"):
            return bd_answer
        else:
            # XXX: pango.ALIGN_RIGHT workaround: using fixed width font and 
            #      right justification here instead.
            return "%5d" % (int(bd_answer))


def get_device_realshortname(block_device):
    """Input a block device and output its shortname, e.g. sda1.

    block_device -- a block device given by its path, 
                    e.g. /dev/disk/by-id/something

    """

    device_abspath = os.path.realpath(block_device)
    if device_abspath.startswith("/dev/sd"):
        return os.path.basename(device_abspath)
    elif device_abspath.startswith("/dev/hd"):
        return os.path.basename(device_abspath)
    elif device_abspath.startswith("/dev/vd"):
        return os.path.basename(device_abspath)
    elif device_abspath.startswith("/dev/mapper"):
#        return "*lvm*"
        return '<span foreground="#00FF00">lvm</span>'
    else:
        return "n/a"

# TODO: replace with pyparted-2+ once documented and VirOS is rebased to f11
def get_device_partition_type(block_device):
    """Input a block device and output its partition flag string.

    block_device -- a block device given by its path name,
                    e.g. /dev/disk/by-id/something-part2

    note: 'wholedisk' is returned for nonpartition devices

    """
   
    block_device_real = os.path.realpath(block_device)

    if block_device.startswith("/dev/mapper"):
        return "n/a"
    end_base_index = block_device.find("-part")
    
    if (end_base_index == -1):
        return '<span foreground="#FF0000">whole disk</span>'
    else:
        base_device = block_device[0:end_base_index]

        base_device_real = os.path.realpath(base_device)

        dev_null = os.open("/dev/null", os.O_WRONLY)
        try:
            helper_proc = subprocess.Popen(["/sbin/fdisk", 
                                            "-l",
                                            base_device_real],
                                           stdout=subprocess.PIPE,
                                           stderr=dev_null)
            helper_out = helper_proc.communicate()[0]
        finally:
            os.close(dev_null)
        
        if helper_proc.returncode:
            return "n/a"
        else:
            # extract desired string from output
            for outline in helper_out.splitlines():
                # check for the target partition in the first word of this 
                # line of output
                outwords = outline.split()
                if (len(outwords) and 
                    (outline.split()[0].find(block_device_real) != -1)):
                    try:
                        outwords.remove("*")
                    except:
                        pass
                    return string.join(outwords[5:], ' ')

        # TODO: handle with exception (really, check for root privs up front)
        return 'n/a'


#############################################################################
#############################################################################
##
## end code -- just notes below
##
#############################################################################
#############################################################################
#
# edunote: I'm going to believe this, and lose this comment when I see it
#          in a more official document.  Seems obviously correct unless
#          value update is not atomic.
#  
#   http://mail.python.org/pipermail/python-list/2008-December/693764.html
#   Is this a theoretical question? What do your readers/writers actually do?
#   Just reading a global variable does not require any locking. If it is  
#   being modified, you either get the previous value, or the new value.

