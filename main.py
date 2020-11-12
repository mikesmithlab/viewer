from pyqt_widgets import QtImageViewer, Spinbox_Slider
from labvision.images import hstack
from readcropvid import ReadCropVideo
from labvision.video import WriteVideo
from labvision.images import save
from crop import SelectAreaWidget
import sys

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QApplication, QHBoxLayout,
                                 QWidget,
                                 QVBoxLayout, QAction, QPushButton, QFileDialog)


import os




class MainWindow(QtImageViewer):
    def __init__(self, filename=None):

        app = QApplication(sys.argv)
        super().__init__()
        if filename is None:
            home = os.getenv("HOME")
            filename, _ = QFileDialog.getOpenFileName(self, "", home + "/Videos/")
        self.filename=filename
        self.setup_main_window()
        self.load_vid()

        sys.exit(app.exec_())


    def setup_main_window(self):
        # Create window and layout


        self.win = QWidget()
        self.vbox = QVBoxLayout(self.win)


        # Create Image viewer
        self.viewer_setup()
        self.vbox.addWidget(self.viewer)
        self.framenum_slider = Spinbox_Slider(self.win, 'frame number', self.slider_update, min=0, max=1, step=1)
        self.crop_button = QPushButton('Crop')
        self.reset_crop_button = QPushButton('Reset')
        self.save_img_button = QPushButton('Save Img')
        self.saveas_button = QPushButton('Save Vid')
        self.load_vid()
        self.framenum_slider.vid_end=self.readvid.num_frames - 1
        self.framenum_slider.set_slider_range(0,self.readvid.num_frames - 1, 1)
        hbox = QHBoxLayout()

        hbox.addWidget(self.framenum_slider)
        hbox.addWidget(self.crop_button)
        hbox.addWidget(self.reset_crop_button)
        hbox.addWidget(self.save_img_button)
        self.crop_button.setCheckable(True)
        self.crop_button.clicked.connect(lambda x=self.crop_button.isChecked, method='crop': self.crop(x))
        self.reset_crop_button.clicked.connect(lambda x:self._set_crop())
        self.save_img_button.clicked.connect(lambda x:self.save_img())
        self.saveas_button.clicked.connect(lambda x:self.save_vid())
        hbox.addWidget(self.saveas_button)
        self.vbox.addLayout(hbox)

        # Finalise window
        self.win.setWindowTitle('ParamGui')
        self.win.setLayout(self.vbox)
        self.win.show()

    def crop(self, check_state):
        self.viewer.canPan = not check_state
        if check_state:
            self.crop_tool = SelectAreaWidget(geometry=self.viewer.geometry)
            self.viewer.scene.addWidget(self.crop_tool)
        else:
            if hasattr(self, 'crop_tool'):
                begin = self.crop_tool.begin
                end = self.crop_tool.end
                if begin.x() < end.x():
                    minx=begin.x()
                    maxx=end.x()
                else:
                    minx = end.x()
                    maxx = begin.x()
                if begin.y() < end.y():
                    miny=begin.y()
                    maxy=end.y()
                else:
                    miny = end.y()
                    maxy = begin.y()
                if maxx-minx < 1:
                    width = 1
                else:
                    width = maxx-minx
                if maxy-miny < 1:
                    height = 1
                else:
                    height=maxy-miny
                crop_coords = ((int(minx), int(minx + width)),(int(miny), int(miny + height)))
                self._set_crop(crop_coords)
                self.crop_tool.setParent(None)
                self.crop_tool.deleteLater()

    def _set_crop(self, crop_coords=None):
        if crop_coords is None:
            self.readvid.reset_crop()
        else:
            self.readvid.set_crop(crop_coords)
        self.load_frame()

    def viewer_setup(self):
        self.viewer = QtImageViewer()
        self.viewer.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.viewer.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        #self.viewer.leftMouseButtonPressed.connect(self.get_coords)
        self.viewer.scrollMouseButton.connect(self._update_frame)
        self.viewer.canZoom = True
        self.viewer.canPan = True
        self.win.resize(1024, 720)


    def setup_menubar(self):
        exitAct = QAction('&Exit', self)
        exitAct.setShortcut('Ctrl+Q')
        exitAct.triggered.connect(app.quit)

        loadVid = QAction('&Load', self)
        loadVid.setShortcut(('Ctrl-O'))
        loadVid.triggered.connect(self.load_video)


        menubar = self.menuBar()
        fileMenu = menubar.addMenu('&File')
        fileMenu.addAction((loadVid))
        fileMenu.addAction(exitAct)

        preferences = menubar.addMenu('&Preferences')

    def load_video(self):
        self.filename=None
        self.load_vid()

    def load_vid(self):
        self.readvid=ReadCropVideo(filename=self.filename)
        self.filename = self.readvid.filename
        self.framenum = 0
        self.framenum_slider.set_slider_range(0, self.readvid.num_frames -1, 1)
        self.load_frame()

    def slider_update(self, val):
        self.framenum = val
        self.load_frame()
        self.framenum_slider.set_slider_value(val)

    def _update_frame(self, wheel_change):
        self.framenum = self.framenum + wheel_change
        if self.framenum < 0:
            self.framenum = 0
        elif self.framenum >= (self.readvid.num_frames - 1):
            self.framenum =  (self.readvid.num_frames - 1)
        self.framenum_slider.set_slider_value(self.framenum)
        self.load_frame()

    def load_frame(self):
        im = self.readvid.read_frame(n=self.framenum)
        self.viewer.setImage(im)

    def _display_img(self, *ims):
        if len(ims) == 1:
            self.im = ims[0]
        else:
            self.im = hstack(*ims)

    def save_vid(self):
        home = os.getenv("HOME")
        filename, ext = QFileDialog.getSaveFileName(self, "", home + "/Videos/",self.tr("*.mp4;; *.m4v;; *.avi"))
        if filename:
            writevid = WriteVideo(filename, frame=self.readvid.read_frame(n=self.framenum_slider.value))
            start = self.framenum_slider.min
            stop =  self.framenum_slider.max
            step = self.framenum_slider.step
            for i in range(start, stop, step):
                img = self.readvid.read_frame(n=i)
                writevid.add_frame(img)
            writevid.close()

    def save_img(self):
        home = os.getenv("HOME")
        filename, ok = QFileDialog.getSaveFileName(self, "", home + "/Pictures/",self.tr("*.jpg;; *.png;; *.tiff"))
        if filename:
            img = self.readvid.read_frame(n=self.framenum_slider.value)
            save(img, filename)






if __name__ == "__main__":
    main = MainWindow()
