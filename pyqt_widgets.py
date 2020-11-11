from PyQt5.QtCore import Qt, pyqtSignal, QRectF
from PyQt5.QtGui import QPixmap, QImage, QPainterPath, QCloseEvent, QWheelEvent
from PyQt5.QtWidgets import (QWidget, QSlider, QCheckBox, QHBoxLayout,
                             QLabel, QComboBox, QSizePolicy, QVBoxLayout,
                             QApplication, QGraphicsView, QGraphicsScene,
                             QLineEdit, QSpinBox, QInputDialog
                             )
import numpy as np
import qimage2ndarray as qim


class Spinbox_Slider(QWidget):
    """
    Groupbox containing slider and spinbox in horizontal layout.
    """

    def __init__(self, parent, title, update_viewer_fn, initial_val = 0, min=0, max=1, step=1, *args, **kwargs):
        self.update_viewer = update_viewer_fn
        super(Spinbox_Slider,self).__init__(*args,**kwargs)

        layout_inner = QHBoxLayout()
        label = QLabel(title)
        layout_inner.addWidget(label)

        self.vid_start=int(min)
        self.vid_end=int(max)
        self.step=step
        self.value = initial_val

        #Slider and spinbox are linked so that they
        #always show same values.
        self.slider=QSlider(Qt.Horizontal)
        self.slider.setValue(initial_val)#slider.setSliderPosition
        self.spinbox = QSpinBox()
        self.spinbox.setValue(initial_val)
        self.set_slider_range(self.vid_start, self.vid_end, step)  # slider.setRange


        layout_inner.addWidget(self.slider)
        layout_inner.addWidget(self.spinbox)

        self.slider.sliderReleased.connect(
            lambda slider_val=self.slider.value: self.value_changed(slider_val)
            )
        self.spinbox.editingFinished.connect(
            lambda spinbox_val=self.spinbox.value: self.value_changed(spinbox_val)
            )
        self.setLayout(layout_inner)

    def value_changed(self, get_value):
        new_value=get_value()
        self.set_slider_value(new_value)
        self.update_viewer(new_value)

    def set_slider_value(self, value):
        self.slider.setValue(value)
        self.spinbox.setValue(value)
        self.value=value

    def set_slider_range(self, start, end, step):

        if start < self.vid_start:
            start=self.vid_start
        if end > self.vid_end:
            end = self.vid_end

        if self.value < start:
            self.value = start
            self.set_slider_value(self.value)
        if self.value > end:
            self.value = end
            self.set_slider_value(self.value)
        self.min=start
        self.max=end
        self.step=step
        self.slider.setRange(start, end)
        self.spinbox.setRange(start,end)

    def mousePressEvent(self, event):
        if event.button() == Qt.RightButton:
            output, ok = QInputDialog.getText(self, 'Enter new range:', 'min,max,step')
            if ok:
                output = output.split(',')
                self.set_slider_range(int(output[0]),int(output[1]), int(output[2]))

        else:
            super().mousePressEvent(event)


class QWidgetMod(QWidget):
    """
    Overrides the closeEvent method of QWidget to print out the parameters set
    in the gui. Is used by ParamGui.
    """

    def __init__(self, param_dict):
        QWidget.__init__(self)
        self.param_dict = param_dict

    def closeEvent(self, a0: QCloseEvent) -> None:
        print('Final Parameters')
        print('------------------------------')
        for key in sorted(self.param_dict.keys()):
            print(key + ' : ' + str(self.param_dict[key][0]))
        print('------------------------------')


class QtImageViewer(QGraphicsView):
    """ PyQt image viewer widget for a QPixmap in a QGraphicsView scene with mouse zooming and panning.
    Displays a QImage or QPixmap (QImage is internally converted to a QPixmap).
    To display any other image format, you must first convert it to a QImage or QPixmap.
    Some useful image format conversion utilities:
        qimage2ndarray: NumPy ndarray <==> QImage    (https://github.com/hmeine/qimage2ndarray)
        ImageQt: PIL Image <==> QImage  (https://github.com/python-pillow/Pillow/blob/master/PIL/ImageQt.py)
    Mouse interaction:
        Left mouse button drag: Pan image.
        Right mouse button drag: Zoom box.
        Right mouse button doubleclick: Zoom to show entire image.
        __author__ = "Marcel Goldschen-Ohm <marcel.goldschen@gmail.com>"
    """

    # Mouse button signals emit image scene (x, y) coordinates.
    # !!! For image (row, column) matrix indexing, row = y and column = x.
    leftMouseButtonPressed = pyqtSignal(float, float)
    rightMouseButtonPressed = pyqtSignal(float, float)
    leftMouseButtonReleased = pyqtSignal(float, float)
    rightMouseButtonReleased = pyqtSignal(float, float)
    leftMouseButtonDoubleClicked = pyqtSignal(float, float)
    rightMouseButtonDoubleClicked = pyqtSignal(float, float)
    scrollMouseButton = pyqtSignal(float)

    def __init__(self):
        QGraphicsView.__init__(self)

        # Image is displayed as a QPixmap in a QGraphicsScene attached to this QGraphicsView.
        self.scene = QGraphicsScene()
        self.setScene(self.scene)

        # Store a local handle to the scene's current image pixmap.
        self._pixmapHandle = None

        # Image aspect ratio mode.
        # !!! ONLY applies to full image. Aspect ratio is always ignored when zooming.
        #   Qt.IgnoreAspectRatio: Scale image to fit viewport.
        #   Qt.KeepAspectRatio: Scale image to fit inside viewport, preserving aspect ratio.
        #   Qt.KeepAspectRatioByExpanding: Scale image to fill the viewport, preserving aspect ratio.
        self.aspectRatioMode = Qt.KeepAspectRatio

        # Scroll bar behaviour.
        #   Qt.ScrollBarAlwaysOff: Never shows a scroll bar.
        #   Qt.ScrollBarAlwaysOn: Always shows a scroll bar.
        #   Qt.ScrollBarAsNeeded: Shows a scroll bar only when zoomed.
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        # Stack of QRectF zoom boxes in scene coordinates.
        self.zoomStack = []

        # Flags for enabling/disabling mouse interaction.
        self.canZoom = True
        self.canPan = True

    def hasImage(self):
        """ Returns whether or not the scene contains an image pixmap.
        """
        return self._pixmapHandle is not None

    def clearImage(self):
        """ Removes the current image pixmap from the scene if it exists.
        """
        if self.hasImage():
            self.scene.removeItem(self._pixmapHandle)
            self._pixmapHandle = None

    def pixmap(self):
        """ Returns the scene's current image pixmap as a QPixmap, or else None if no image exists.
        :rtype: QPixmap | None
        """
        if self.hasImage():
            return self._pixmapHandle.pixmap()
        return None

    def image(self):
        """ Returns the scene's current image pixmap as a QImage, or else None if no image exists.
        :rtype: QImage | None
        """
        if self.hasImage():
            return self._pixmapHandle.pixmap().toImage()
        return None

    def QPixmapToArray(self, pixmap):
        ## Get the size of the current pixmap
        size = pixmap.size()
        h = size.width()
        w = size.height()

        ## Get the QImage Item and convert it to a byte string
        qimg = pixmap.toImage()
        byte_str = qimg.bits().tobytes()
        ## Using the np.frombuffer function to convert the byte string into an np array
        img = np.frombuffer(byte_str, dtype=np.uint8).reshape((w, h, 4))
        return img

    def setImage(self, image):
        """ Set the scene's current image pixmap to the input QImage or QPixmap.
        Raises a RuntimeError if the input image has type other than QImage or QPixmap.
        :type image: QImage | QPixmap
        """
        self.image = image
        print(np.shape(image))
        if type(image) is QPixmap:
            pixmap = image
        elif type(image) is QImage:
            pixmap = QPixmap.fromImage(image)
        elif type(image) is np.ndarray:
            pixmap = QPixmap.fromImage(qim.array2qimage(image))
        else:
            raise RuntimeError("ImageViewer.setImage: Argument must be a QImage or QPixmap.")
        self.geometry = pixmap.rect()
        if self.hasImage():
            self._pixmapHandle.setPixmap(pixmap)
        else:
            self._pixmapHandle = self.scene.addPixmap(pixmap)
        self.setSceneRect(QRectF(pixmap.rect()))  # Set scene size to image size.
        self.updateViewer()

    def updateViewer(self):
        """ Show current zoom (if showing entire image, apply current aspect ratio mode).
        """
        if not self.hasImage():
            return
        if len(self.zoomStack) and self.sceneRect().contains(self.zoomStack[-1]):
            self.fitInView(self.zoomStack[-1],
                           Qt.KeepAspectRatio)  # Qt.IgnoreAspectRatio)  # Show zoomed rect (ignore aspect ratio).
        else:
            self.zoomStack = []  # Clear the zoom stack (in case we got here because of an invalid zoom).
            self.fitInView(self.sceneRect(), self.aspectRatioMode)  # Show entire image (use current aspect ratio mode).

    def resizeEvent(self, event):
        """ Maintain current zoom on resize.
        """
        self.updateViewer()

    def mousePressEvent(self, event):
        """ Start mouse pan or zoom mode.
        """
        scenePos = self.mapToScene(event.pos())
        if event.button() == Qt.LeftButton:
            if self.canPan:
                self.setDragMode(QGraphicsView.ScrollHandDrag)
            self.leftMouseButtonPressed.emit(scenePos.x(), scenePos.y())
            print('Pixel Coords:')
            print('(' + str(scenePos.x()) + ',' + str(scenePos.y()) + ')')
            print('Pixel Intensities:')
            print(self.image[int(scenePos.y()), int(scenePos.x()),:])
            print('\n')
        elif event.button() == Qt.RightButton:
            if self.canZoom:
                self.setDragMode(QGraphicsView.RubberBandDrag)
            self.rightMouseButtonPressed.emit(scenePos.x(), scenePos.y())
        QGraphicsView.mousePressEvent(self, event)

    def mouseReleaseEvent(self, event):
        """ Stop mouse pan or zoom mode (apply zoom if valid).
        """
        QGraphicsView.mouseReleaseEvent(self, event)
        scenePos = self.mapToScene(event.pos())
        if event.button() == Qt.LeftButton:
            self.setDragMode(QGraphicsView.NoDrag)
            self.leftMouseButtonReleased.emit(scenePos.x(), scenePos.y())
        elif event.button() == Qt.RightButton:
            if self.canZoom:
                viewBBox = self.zoomStack[-1] if len(self.zoomStack) else self.sceneRect()
                selectionBBox = self.scene.selectionArea().boundingRect().intersected(viewBBox)
                self.scene.setSelectionArea(QPainterPath())  # Clear current selection area.
                if selectionBBox.isValid() and (selectionBBox != viewBBox):
                    self.zoomStack.append(selectionBBox)
                    self.updateViewer()
            self.setDragMode(QGraphicsView.NoDrag)
            self.rightMouseButtonReleased.emit(scenePos.x(), scenePos.y())

    def mouseDoubleClickEvent(self, event):
        """ Show entire image.
        """
        scenePos = self.mapToScene(event.pos())
        if event.button() == Qt.LeftButton:
            self.leftMouseButtonDoubleClicked.emit(scenePos.x(), scenePos.y())
        elif event.button() == Qt.RightButton:
            if self.canZoom:
                self.zoomStack = []  # Clear zoom stack.
                self.updateViewer()
            self.rightMouseButtonDoubleClicked.emit(scenePos.x(), scenePos.y())
        QGraphicsView.mouseDoubleClickEvent(self, event)

    def wheelEvent(self, event: QWheelEvent):
        self.scrollMouseButton.emit(int(event.angleDelta().y() / 120))
        QGraphicsView.wheelEvent(self, event)

