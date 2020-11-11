from labvision.video import ReadVideo


class ReadCropVideo(ReadVideo):

    def __init__(self, filename=None, frame_range=(0,None,1)):
        ReadVideo.__init__(self, filename=filename, frame_range=frame_range)

        '''
        If loading a new video with different dimensions,
        then the stored crop and mask parameters may not fit.
        Perform a check. If fails reset crop and mask to frame
        dimensions. This may not sort the gui but it will stop
        a crash.
        '''
        self.reset_crop()

    def set_crop(self, crop_coords):
        #Crops image to size specified by crop_coords and sets mask to None.
        self.crop_vals = crop_coords
        print(self.crop_vals)

    def reset_crop(self):
        #To set crop back to max image size
        self.set_crop(((0, self.width),(0, self.height)))


    def read_frame(self, n=None):
        frame = super().read_frame(n=n)
        frame = frame[self.crop_vals[1][0]:self.crop_vals[1][1], self.crop_vals[0][0]: self.crop_vals[0][1],:]
        return frame



