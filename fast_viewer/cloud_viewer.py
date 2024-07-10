#!/usr/bin/env python3

import numpy as np
from fast_viewer.custom_items import *
from fast_viewer.basic_window import *
from pypcd4 import PointCloud


class CloudViewer(Viewer):
    def __init__(self):
        super(CloudViewer, self).__init__(name="Cloud Viewer")
        self.setAcceptDrops(True)

    def follow(self, p):
        self.viewer.setCameraPosition(pos=QVector3D(p[0], p[1], p[2]))

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            self.openCloudFile(file_path)

    def openCloudFile(self, file):
            cloud_item = self['cloud']
            if cloud_item is None:
                print("Can't find clouditem")
                return

            print("Try to load %s ..." % file)
            pc = PointCloud.from_path(file).pc_data

            try:
                color = pc["rgb"].astype(np.uint32)
                cloud_item.setColorMode(-2)
            except ValueError:
                try:
                    color = pc["intensity"].astype(np.uint32)
                    cloud_item.setColorMode(-1)
                except ValueError:
                    color = pc['z'].astype(np.uint32)
                    cloud_item.setColorMode('#FFFFFF')

            cloud = np.rec.fromarrays(
                [np.stack([pc["x"], pc["y"], pc["z"]], axis=1), color], 
                dtype=cloud_item.data_type)
            cloud_item.setData(data=cloud)


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--pcd", help="the pcd path")
    args = parser.parse_args()
    app = QApplication([])
    viewer = CloudViewer()

    cloudItem = CloudItem(size=1, alpha=0.1)
    axisItem = GLAxisItem(size=0.5, width=5)
    gridItem = GridItem(size=1000, spacing=20)

    viewer.addItems(grid=gridItem, axis=axisItem, cloud=cloudItem)

    if args.pcd:
        pcd_fn = args.pcd
        viewer.openCloudFile(pcd_fn)

    viewer.show()
    app.exec_()


if __name__ == '__main__':
    main()
