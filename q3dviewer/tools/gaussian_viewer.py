#!/usr/bin/env python3

"""
Copyright 2024 Panasonic Advanced Technology Development Co.,Ltd. (Liu Yang)
Distributed under MIT license. See LICENSE for more information.
"""

import numpy as np
import q3dviewer as q3d
from q3dviewer.gau_io import load_gs, rotate_gaussian


class GuassianViewer(q3d.Viewer):
    def __init__(self, **kwds):
        super(GuassianViewer, self).__init__(**kwds)
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            self.openGSFile(file_path)

    def openGSFile(self, file):
        gau_item = self['gaussian']
        if gau_item is None:
            print("Can't find gaussianitem")
            return

        print("Try to load %s ..." % file)
        gs = load_gs(file)
        # convert camera optical frame (b) to camera frame (c).
        Rcb = np.array([[0, -1, 0],
                        [0, 0, -1],
                        [1, 0, 0]]).T
        gs = rotate_gaussian(Rcb, gs)
        gs_data = gs.view(np.float32).reshape(gs.shape[0], -1)
        gau_item.setData(gs_data=gs_data)


def main():
    app = q3d.QApplication(['Guassian Viewer'])
    viewer = GuassianViewer(name='Guassian Viewer')

    grid_item = q3d.GridItem(size=1000, spacing=20)
    gau_item = q3d.GaussianItem()

    viewer.addItems({'grid': grid_item, 'gaussian': gau_item})

    viewer.show()
    app.exec_()


if __name__ == '__main__':
    main()
