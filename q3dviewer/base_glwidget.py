from OpenGL.GL import *  # noqa
import OpenGL.GL.framebufferobjects as glfbo  # noqa
from math import cos, radians, sin, tan

import numpy as np

from pyqtgraph import Vector
from pyqtgraph import functions as fn
from pyqtgraph import getConfigOption
from PyQt5 import QtCore, QtGui, QtWidgets

from q3dviewer.utils import frustum, euler_to_matrix, make_transform, makeT, m_get_roll  # Import euler_to_matrix function
from PyQt5.QtGui import QKeyEvent, QVector3D, QMatrix4x4

class BaseGLWidget(QtWidgets.QOpenGLWidget):
    
    def __init__(self, parent=None):
        QtWidgets.QOpenGLWidget.__init__(self, parent)
        self.setFocusPolicy(QtCore.Qt.FocusPolicy.ClickFocus)
        self._fov = 60
        self.reset()
        self.items = []
        self.noRepeatKeys = [QtCore.Qt.Key.Key_Right, QtCore.Qt.Key.Key_Left, QtCore.Qt.Key.Key_Up, QtCore.Qt.Key.Key_Down, QtCore.Qt.Key.Key_PageUp, QtCore.Qt.Key.Key_PageDown]
        self.keysPressed = {}
        self.keyTimer = QtCore.QTimer()
        self.color = np.array([0, 0, 0, 0])
        self.Twb = makeT(euler_to_matrix([0, 0, 0]), np.array([-0, -50, 20]))
        self.Tbc = makeT(euler_to_matrix([np.pi/3, 0, 0]), np.array([0, 0, 0]))
        self.active_keys = set()

    def keyPressEvent(self, ev: QKeyEvent):
        if ev.key() == QtCore.Qt.Key_Up or  \
            ev.key() == QtCore.Qt.Key_Down or \
            ev.key() == QtCore.Qt.Key_Left or \
            ev.key() == QtCore.Qt.Key_Right or \
            ev.key() == QtCore.Qt.Key_Z or \
            ev.key() == QtCore.Qt.Key_X or \
            ev.key() == QtCore.Qt.Key_A or \
            ev.key() == QtCore.Qt.Key_D or \
            ev.key() == QtCore.Qt.Key_W or \
            ev.key() == QtCore.Qt.Key_S:
            self.active_keys.add(ev.key())
        self.active_keys.add(ev.key())

    def keyReleaseEvent(self, ev: QKeyEvent):
        self.active_keys.discard(ev.key())

    def deviceWidth(self):
        dpr = self.devicePixelRatioF()
        return int(self.width() * dpr)

    def deviceHeight(self):
        dpr = self.devicePixelRatioF()
        return int(self.height() * dpr)

    def reset(self):
        """
        Initialize the widget state or reset the current state to the original state.
        """
        pass
        # self.opts['center'] = Vector(0,0,0)  ## will always appear at the center of the widget
        # self._dist = 10.0         ## distance of camera from center
        # self._fov = 60                ## horizontal field of view in degrees
        # self.opts['elevation'] = 30          ## camera's angle of elevation in degrees
        # self.opts['azimuth'] = 45            ## camera's azimuthal angle in degrees 
        #                                      ## (rotation around z-axis 0 points along x-axis)
        # self.opts['viewport'] = None         ## glViewport params; None == whole widget
        # self.set_color(np.array([0, 0, 0, 0]))

    def addItem(self, item):
        self.items.append(item)

        if self.isValid():
            item.initialize()
                
        item._setView(self)
        self.update()
        
    def removeItem(self, item):
        """
        Remove the item from the scene.
        """
        self.items.remove(item)
        item._setView(None)
        self.update()

    def clear(self):
        """
        Remove all items from the scene.
        """
        for item in self.items:
            item._setView(None)
        self.items = []
        self.update()        
        
    def initializeGL(self):
        for item in self.items:
            if not item.isInitialized():
                item.initialize()
        
    def set_color(self, color):
        self.color = color
        self.update()

    def update(self):
        self.updateMovement()
        super().update()

    def setProjection(self, region=None):
        m = self.projectionMatrix(region)
        glMatrixMode(GL_PROJECTION)
        glLoadMatrixf(m.T)

    def projectionMatrix(self, region=None):
        w, h = self.deviceWidth(), self.deviceHeight()
        dist = np.abs(self.Twb[2, 3])
        near = dist * 0.001
        far = dist * 10000.
        r = near * tan(0.5 * radians(self._fov))
        t = r * h / w
        matrix = frustum(-r, r, -t, t, near, far)
        return matrix

    def get_focal(self):
        width = self.deviceWidth()
        height = self.deviceHeight()
        fx = 0.5 * width / tan(radians(self._fov) / 2)
        fy = 0.5 * height / tan(radians(self._fov) / 2)
        return np.array([fx, fy])

    def mouseReleaseEvent(self, ev):
        if hasattr(self, 'mousePos'):
            delattr(self, 'mousePos')

    def mouseMoveEvent(self, ev):
        lpos = ev.localPos()
        if not hasattr(self, 'mousePos'):
            self.mousePos = lpos
        diff = lpos - self.mousePos
        self.mousePos = lpos
        if ev.buttons() == QtCore.Qt.MouseButton.RightButton:
            dR = euler_to_matrix([-diff.y() * 0.005, 0, 0])
            self.Tbc[:3, :3] = self.Tbc[:3, :3] @ dR
            dR = euler_to_matrix([0, 0, -diff.x() * 0.005])
            self.Twb[:3, :3] = self.Twb [:3, :3] @ dR
        elif ev.buttons() == QtCore.Qt.MouseButton.LeftButton:
            width = self.deviceWidth()
            project_matrix = self.projectionMatrix()
            focal = project_matrix[0, 0] * width / 2
            z = np.abs(self.Twb[2, 3])
            roll = np.abs(m_get_roll(self.Tbc))
            print(roll)
            if (roll < 1.3):
                dtrans = np.array([-diff.x() * z / focal, diff.y()* z / focal, 0])
                self.Twb[:3, 3] += self.Twb[:3, :3] @ dtrans
            else:
                dtrans = np.array([-diff.x() / focal * 50, 0, diff.y() / focal * 50])
                self.Twb[:3, 3] += self.Twb[:3, :3] @ dtrans


    def updateMovement(self):
        if self.active_keys == {}:
            return
        rotation_speed = 0.01
        trans_speed = 1
        z = np.abs(self.Twb[2, 3])
        if z < 20:
            trans_speed = z * 0.05
        if QtCore.Qt.Key_Up in self.active_keys:
            dR = euler_to_matrix([rotation_speed, 0, 0])
            self.Tbc[:3, :3] = self.Tbc[:3, :3] @ dR
        if QtCore.Qt.Key_Down in self.active_keys:
            dR = euler_to_matrix([-rotation_speed, 0, 0])
            self.Tbc[:3, :3] = self.Tbc[:3, :3] @ dR
        if QtCore.Qt.Key_Left in self.active_keys:
            dR = euler_to_matrix([0, 0, rotation_speed])
            self.Twb[:3, :3] = self.Twb [:3, :3]@ dR
        if QtCore.Qt.Key_Right in self.active_keys:
            dR = euler_to_matrix([0, 0, -rotation_speed])
            self.Twb[:3, :3] = self.Twb[:3, :3] @ dR
        if QtCore.Qt.Key_Z in self.active_keys:
            self.Twb[:3, 3] += self.Twb[:3, :3] @ self.Tbc[:3, :3] @ np.array([0, 0, +trans_speed])
        if QtCore.Qt.Key_X in self.active_keys:
            self.Twb[:3, 3] += self.Twb[:3, :3] @ self.Tbc[:3, :3] @ np.array([0, 0, -trans_speed])
        if QtCore.Qt.Key_A in self.active_keys:
            self.Twb[:3, 3] += self.Twb[:3, :3] @ np.array([-trans_speed, 0, 0])
        if QtCore.Qt.Key_D in self.active_keys:
            self.Twb[:3, 3] += self.Twb[:3, :3] @ np.array([trans_speed, 0, 0])
        if QtCore.Qt.Key_W in self.active_keys:
            self.Twb[:3, 3] += self.Twb[:3, :3] @ np.array([0, trans_speed, 0])
        if QtCore.Qt.Key_S in self.active_keys:
            self.Twb[:3, 3] += self.Twb[:3, :3] @ np.array([0, -trans_speed, 0])

    def wheelEvent(self, ev):
        delta = ev.angleDelta().x()
        if delta == 0:
            delta = ev.angleDelta().y()
        delta = delta * 0.03
        self.Twb[:3, 3] += self.Twb[:3, :3] @ self.Tbc[:3, :3] @ np.array([0, 0, -delta])
        self.update()


    def setModelview(self):
        m = self.viewMatrix()
        glMatrixMode(GL_MODELVIEW)
        glLoadMatrixf(m.T)
        
    def viewMatrix(self):
        # Create a 4x4 identity matrix
        return np.linalg.inv(self.Twb @ self.Tbc)

    def itemsAt(self, region=None):
        """
        Return a list of the items displayed in the region (x, y, w, h)
        relative to the widget.        
        """
        region = (region[0], self.deviceHeight()-(region[1]+region[3]), region[2], region[3])
        
        #buf = np.zeros(100000, dtype=np.uint)
        buf = glSelectBuffer(100000)
        try:
            glRenderMode(GL_SELECT)
            glInitNames()
            glPushName(0)
            self._itemNames = {}
            self.paintGL(region=region, useItemNames=True)
            
        finally:
            hits = glRenderMode(GL_RENDER)
            
        items = [(h.near, h.names[0]) for h in hits]
        items.sort(key=lambda i: i[0])
        return [self._itemNames[i[1]] for i in items]
    
    def paintGL(self, region=None, viewport=None, useItemNames=False):
        """
        viewport specifies the arguments to glViewport. If None, then we use self.opts['viewport']
        region specifies the sub-region of self.opts['viewport'] that should be rendered.
        Note that we may use viewport != self.opts['viewport'] when exporting.
        """
        self.setProjection(region=region)
        self.setModelview()
        bgcolor = self.color
        glClearColor(*bgcolor)
        glClear( GL_DEPTH_BUFFER_BIT | GL_COLOR_BUFFER_BIT )
        self.drawItemTree(useItemNames=useItemNames)
        
    def drawItemTree(self, item=None, useItemNames=False):
        if item is None:
            items = [x for x in self.items if x.parentItem() is None]
        else:
            items = item.childItems()
            items.append(item)
        items.sort(key=lambda a: a.depthValue())
        for i in items:
            if not i.visible():
                continue
            if i is item:
                try:
                    glPushAttrib(GL_ALL_ATTRIB_BITS)
                    if useItemNames:
                        glLoadName(i._id)
                        self._itemNames[i._id] = i
                    i.paint()
                except:
                    from .. import debug
                    debug.printExc()
                    print("Error while drawing item %s." % str(item))
                    
                finally:
                    glPopAttrib()
            else:
                glMatrixMode(GL_MODELVIEW)
                glPushMatrix()
                try:
                    tr = i.transform()
                    glMultMatrixf(np.array(tr.data(), dtype=np.float32))
                    self.drawItemTree(i, useItemNames=useItemNames)
                finally:
                    glMatrixMode(GL_MODELVIEW)
                    glPopMatrix()
            

    def rotate(self, rx=0, ry=0, rz=0):
        # update the euler angles
        self.euler += np.radians(np.array([rx, ry, rz]).astype(np.float32))
        self.euler = (self.euler + np.pi) % (2 * np.pi) - np.pi
        self.update()
