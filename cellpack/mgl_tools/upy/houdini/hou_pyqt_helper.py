
"""
    Copyright (C) <2010>  Autin L. TSRI
    
    This file git_upy/houdini/hou_pyqt_helper.py is part of upy.

    upy is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    upy is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with upy.  If not, see <http://www.gnu.org/licenses/gpl-3.0.html>.
"""
"""
This module helps you use PyQt in Houdini's GUI by integrating PyQt's event
loop into Houdini's.  Replace calls to QApplication.exec_() in your
code with calls to pyqt_houdini.exec_(app).
"""

from PyQt4 import QtCore
from PyQt4 import QtGui
import hou

class IntegratedEventLoop(object):
    """This class behaves like QEventLoop except it allows PyQt to run inside
       Houdini's event loop on the main thread.  You probably just want to
       call exec_() below instead of using this class directly."""
    def __init__(self, application, dialogs):
        # We need the application to send posted events.  We hold a reference
        # to any dialogs to ensure that they don't get garbage collected
        # (and thus close in the process).  The reference count for this object
        # will go to zero when it removes itself from Houdini's event loop.
        self.application = application
        self.dialogs = dialogs
        self.event_loop = QtCore.QEventLoop()

    def exec_(self):
        hou.ui.addEventLoopCallback(self.processEvents)

    def processEvents(self):
        # There is no easy way to know when the event loop is done.  We can't
        # use QEventLoop.isRunning() because it always returns False since
        # we're not inside QEventLoop.exec_().  We can't rely on a
        # lastWindowClosed signal because the window is usually made invisible
        # instead of closed.  Instead, we need to explicitly check if any top
        # level widgets are still visible.
        if True not in (w.isVisible() for w in QtGui.QApplication.topLevelWidgets()):
            hou.ui.removeEventLoopCallback(self.processEvents)

        self.event_loop.processEvents()
        self.application.sendPostedEvents(None, 0)

def exec_(application, *args):
    """You cannot call QApplication.exec_, or Houdini will freeze while PyQt
       waits for and processes events.  Instead, call this function to allow
       Houdini's and PyQt's event loops to coexist.  Pass in any dialogs as
       extra arguments, if you want to ensure that something holds a reference
       to them while the event loop runs.

       This function returns right away."""
    IntegratedEventLoop(application, args).exec_()
