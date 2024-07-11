#!/usr/bin/env python3

import numpy as np
from fast_viewer.custom_items import *
from fast_viewer.basic_window import *
from pyqtgraph.opengl import GLMeshItem
from stl import mesh


class MeshViewer(Viewer):
    def __init__(self):
        super(MeshViewer, self).__init__(name="Mesh Viewer")
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            self.openMeshFile(file_path)

    def openMeshFile(self, file):
            mesh_item = self['mesh']
            if mesh_item is None:
                print("Can't find meshitem")
                return

            print("Try to load %s ..." % file)
            stl_mesh = mesh.Mesh.from_file(file)

            vertices = stl_mesh.points.reshape(-1, 3)
            faces = np.arange(vertices.shape[0]).reshape(-1, 3)
            mesh_item.setMeshData(vertexes=vertices, faces=faces)


def main():
    app = QApplication([])
    viewer = MeshViewer()

    gridItem = GridItem(size=1000, spacing=20)
    # 'glOptions', 'opaque', 'additive' 'translucent'
    meshItem = GLMeshItem(smooth=True, drawFaces=True, drawEdges=True,
                          color=(0, 1, 0, 0.2), edgeColor=(1, 1, 1, 1), glOptions='translucent')

    viewer.addItems({'grid': gridItem, 'mesh': meshItem})

    viewer.show()
    app.exec_()


if __name__ == '__main__':
    main()
