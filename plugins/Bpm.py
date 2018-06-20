############################################################################
# This file is part of LImA, a Library for Image Acquisition
#
# Copyright (C) : 2009-2018
# European Synchrotron Radiation Facility
# BP 220, Grenoble 38043
# FRANCE
#
# This is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This software is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, see <http://www.gnu.org/licenses/>.
############################################################################

import itertools
import weakref
import PyTango
import sys
import numpy
import processlib
import time
import struct
from Lima import Core
from Lima.Server.plugins.Utils import BasePostProcess
#pixmaptools
import os
try:
    from bliss.data.routines.pixmaptools import qt4 as pixmaptools
except ImportError:
    os.environ["QUB_SUBPATH"]="qt4"
    from Qub.CTools import pixmaptools #for 16-bits to 8-bits conversionimport time
import Image
import cStringIO
import base64



def grouper(n, iterable, padvalue=None):
    return itertools.izip(*[itertools.chain(iterable, itertools.repeat(padvalue, n-1))]*n)



#==================================================================
#   Bpm Class Description:
#
#
#==================================================================


class BpmDeviceServer(BasePostProcess):

#--------- Add you global variables here --------------------------
    BPM_TASK_NAME = "BpmTask"
    BVDATA_TASK_NAME = "BVDataTask"
#------------------------------------------------------------------
#    Device constructor
#------------------------------------------------------------------
    def __init__(self,cl, name):
        self._softOp = None
        self._bpmManager = None
        self.bvdata = None
        self.autoscale = False
        self.color_map = False
        self.lut_method = "LINEAR"
        self._BVDataTask = None
#######PALETTE INIT
        color_palette =  pixmaptools.LUT.Palette(pixmaptools.LUT.Palette.TEMP)
        greyscale_palette = pixmaptools.LUT.Palette(pixmaptools.LUT.Palette.GREYSCALE)
        a = numpy.fromstring(color_palette.getPaletteData(), dtype=numpy.uint8)
        a.shape = (65536, 4)
        # BGR<=>RGB conversion
        r = numpy.array(a.T[2])
        b = numpy.array(a.T[0])
        a.T[0]=r; a.T[2]=b
        color_palette.setPaletteData(a)
        self.palette = { pixmaptools.LUT.Palette.TEMP: color_palette, pixmaptools.LUT.Palette.GREYSCALE: greyscale_palette }
#######
        BasePostProcess.__init__(self,cl,name)
        self.init_device()


    def init_device(self):
        print "In ", self.get_name(), "::init_device()"
        self.get_device_properties(self.get_device_class())

        for attr in ("intensity", "proj_x", "proj_y",
                     "fwhm_x", "fwhm_y", "txy", "x", "y", "bvdata"):
            self.set_change_event(attr, True, False)


    def set_state(self,state) :
        if(state == PyTango.DevState.OFF) :
            if(self._softOp) :
                self._softOp = None
                self._bpmManager = None
                self._BVDataTask = None
                ctControl = _control_ref()
                extOpt = ctControl.externalOperation()
                extOpt.delOp(self.BVDATA_TASK_NAME)
                extOpt.delOp(self.BPM_TASK_NAME)
        elif(state == PyTango.DevState.ON) :
            if not self._bpmManager:
                ctControl = _control_ref()
                extOpt = ctControl.externalOperation()
                self._softOp = extOpt.addOp(Core.BPM,self.BPM_TASK_NAME,
                                                    self._runLevel)
                self._bpmManager = self._softOp.getManager()
                self._BVDataTask = BVDataTask(self._bpmManager,self)
                handler = extOpt.addOp(Core.USER_SINK_TASK,
                                       self.BVDATA_TASK_NAME,self._runLevel+1)
                handler.setSinkTask(self._BVDataTask)


        PyTango.Device_4Impl.set_state(self,state)

#------------------------------------------------------------------
#    Read buffersize attribute
#------------------------------------------------------------------
    def read_buffersize(self, attr):
        value_read = self._bpmManager.historySize()
        attr.set_value(value_read)


#------------------------------------------------------------------
#    Write buffersize attribute
#------------------------------------------------------------------
    def write_buffersize(self, attr):
        data = attr.get_write_value()
        self._bpmManager.resizeHistory(data)



#==================================================================
#
#    Bpm command methods
#
#==================================================================
    def validate_number(self, x, fallback_value=-1, min_value=0, max_value=None):
        if x is None:
          return fallback_value
        if not numpy.isfinite(x):
          return fallback_value
        if numpy.isnan(x):
          return fallback_value
        if min_value is not None and x < min_value:
          return fallback_value
        if max_value is not None and x > max_value:
          return fallback_value
        return x

    def getResults(self, from_index=0) :
        results = self._bpmManager.getHistory(from_index)
        result_array = numpy.zeros((len(results),7))
        dim = _control_ref().image().getImageDim().getSize()
        max_width = dim.getWidth()
        max_height = dim.getHeight()
        for i,r in enumerate(results):
            result_array[i][0] = r.timestamp
            result_array[i][1] = self.validate_number(r.beam_intensity)
            result_array[i][2] = self.validate_number(r.beam_center_x, max_value=max_width)
            result_array[i][3] = self.validate_number(r.beam_center_y, max_value=max_height)
            result_array[i][4] = self.validate_number(r.beam_fwhm_x, fallback_value=0)
            result_array[i][5] = self.validate_number(r.beam_fwhm_y, fallback_value=0)
            result_array[i][6] = r.frameNumber
        return result_array.ravel()

    def GetPixelIntensity(self, coordinate):
        x=coordinate[0] ; y=coordinate[1]
        try:
            image = _control_ref().ReadImage()
            raw_image = image.buffer.copy()
            return int(raw_image[x][y])
        except:
            return -1
 

    """
##############BACKGROUND : will see later
    def take_background(self):
        if self.getAcqStatus()=='Running':
            raise RuntimeError, "Acquisition has not finished (or Live mode is on)"
        self.get_position()
        self._set_background()


    def _set_background(self):
        if self.bkg_substraction_handler is not None:
            self._ext.delOp("bkg")
        im = self.ccd_control.ReadImage()
        self.bkg_substraction_handler = self._ext.addOp(self.Lima.Core.BACKGROUNDSUBSTRACTION, "bkg", 0)
        self.bkg_substraction_handler.setBackgroundImage(im)
        self._ext_change_event.set()


    def _has_background(self):
        return self.bkg_substraction_handler is not None


    def reset_background(self):
        if self.bkg_substraction_handler is not None:
            self._ext.delOp("bkg")
        self.bkg_substraction_handler = None
        self._ext_change_event.set()
##############
    """

#==================================================================
#
#    BpmDeviceServer read/write attribute methods
#
#==================================================================
    #
    def get_bpm_result(self, frameNumber=None, timestamp=None):
        if frameNumber==None:
            t = time.time()
            result = self._bpmManager.getResult()
        else:
            t = timestamp
            result = self._bpmManager.getResult(0,frameNumber)
        dim = _control_ref().image().getImageDim().getSize()
        max_width = dim.getWidth()
        max_height = dim.getHeight()
        if result.errorCode != self._bpmManager.OK:
           x = -1
           y = -1
           intensity = -1
           fwhm_x = 0
           fwhm_y = 0
           max_intensity = 0
        else:
            x  = self.validate_number(result.beam_center_x, max_value=max_width)
            y  = self.validate_number(result.beam_center_y, max_value=max_height)
            intensity = self.validate_number(result.beam_intensity)
            fwhm_x = self.validate_number(result.beam_fwhm_x, fallback_value=0)
            fwhm_y = self.validate_number(result.beam_fwhm_y, fallback_value=0)
            max_intensity = self.validate_number(result.max_pixel_value, fallback_value=0)
        try:
            profile_x = result.profile_x.buffer.astype(numpy.int)
        except:
            profile_x = numpy.array([],dtype=numpy.int)
        try:
            profile_y = result.profile_y.buffer.astype(numpy.int)
        except:
            profile_y = numpy.array([],dtype=numpy.int)
        
        acq_time=t
        result_array = [acq_time,x,y,intensity,fwhm_x,fwhm_y,max_intensity,profile_x,profile_y]
        return result_array


    def read_txy(self, attr):
        last_acq_time, last_x, last_y, _, _, _, _, _, _ = self.get_bpm_result()
        value = numpy.array([last_acq_time, last_x, last_y], numpy.double)
        attr.set_value(value)

    def read_x(self, attr):
        _, last_x, _, _, _, _, _, _, _ = self.get_bpm_result()
        attr.set_value(last_x)

    def read_y(self, attr):
        _, _, last_y, _, _, _, _, _, _ = self.get_bpm_result()
        attr.set_value(last_y)

    def read_intensity(self, attr):
        _, _, _, last_intensity, _, _, _, _, _ = self.get_bpm_result()
        attr.set_value(last_intensity)

    def read_fwhm_x(self, attr):
        _, _, _, _, last_fwhm_x, _, _, _, _ = self.get_bpm_result()
        attr.set_value(last_fwhm_x)

    def read_fwhm_y(self, attr):
        _, _, _, _, _, last_fwhm_y, _, _, _ = self.get_bpm_result()
        attr.set_value(last_fwhm_y)

    def read_max_intensity(self, attr):
        _, _, _, _, _, _, last_max_intensity, _, _ = self.get_bpm_result()
        attr.set_value(last_max_intensity)

    def read_proj_x(self, attr):
        _, _, _, _, _, _, _, last_proj_x, _ = self.get_bpm_result()
        attr.set_value(last_proj_x)

    def read_proj_y(self, attr):
        _, _, _, _, _, _, _, _, last_proj_y = self.get_bpm_result()
        attr.set_value(last_proj_y)

    def read_automaticaoi(self,attr):
        aoi = self._softOp.getTask().mRoiAutomatic
        attr.set_value(aoi)

    def write_automaticaoi(self,attr):
        aoi = attr.get_write_value()
        self._softOp.getTask().mRoiAutomatic = aoi

    def read_autoscale(self,attr):
        attr.set_value(self.autoscale)

    def write_autoscale(self,attr):
        data = attr.get_write_value()
        self.autoscale = data

    def read_lut_method(self,attr):
        attr.set_value(self.lut_method)

    def write_lut_method(self,attr):
        data = attr.get_write_value()
        if data == "LINEAR" or data == "LOG":
            self.lut_method=data
        else:
            print "wrong lut method" #maybe error message
    
    def read_color_map(self,attr):
        attr.set_value(self.color_map)

    def write_color_map(self,attr):
        data = attr.get_write_value()
        self.color_map=data

    def read_calibration(self, attr):
        if None not in self.calibration:
            attr.set_value(self.calibration)

    
    def write_calibration(self, attr):
        data = attr.get_write_value()
        self.calibration = data

        
    def read_beammark(self, attr):
        if None not in self.beammark:
            attr.set_value(self.beammark)
    
    def write_beammark(self, attr):
        data = attr.get_write_value()
        self.beammark[0] = data[0]
        self.beammark[1] = data[1]



#need to see how bpm will deal with bvdata 
    def read_bvdata(self,attr):
 
        self.bvdata = None
        self.bvdata_format = None
        self.bvdata, self.bvdata_format = construct_bvdata(self)
        
        attr.set_value(self.bvdata_format,self.bvdata)


#==================================================================
#
#    BpmClass class definition
#
#==================================================================
class BpmDeviceServerClass(PyTango.DeviceClass):

    #	 Class Properties
    class_property_list = {
	}


    #	 Device Properties
    device_property_list = {
        "calibration":
        [PyTango.DevVarDoubleArray,
        "Array containing calibX and calibY",
        [1.0,1.0] ],
        "beammark":
        [PyTango.DevVarLongArray,
        "Array containing BeamMark positions (X,Y)",
        [0,0] ]
	}


    #	 Command definitions
    cmd_list = {
        'getResults':
            [[PyTango.DevLong,"from frame number"],
             [PyTango.DevVarDoubleArray,"frame number,x,y"]],
	    'Start':
            [[PyTango.DevVoid,"Start Bpm device"],
             [PyTango.DevVoid,""]],
	    'Stop':
            [[PyTango.DevVoid,"Stop Bpm device"],
             [PyTango.DevVoid,""]],
        'GetPixelIntensity':
            [[PyTango.DevVarLongArray, "pixel coordinate"],
             [PyTango.DevLong, "return intensity on last image"]]

	}


    #	 Attribute definitions
    attr_list = {
        'buffersize': [[PyTango.DevLong, PyTango.SCALAR, PyTango.READ_WRITE]],
        'txy': [[PyTango.DevDouble, PyTango.SPECTRUM, PyTango.READ, 3 ]],
        'x': [[PyTango.DevDouble, PyTango.SCALAR, PyTango.READ ]],
        'y': [[PyTango.DevDouble, PyTango.SCALAR, PyTango.READ ]],
#        'AcquisitionSpectrum': [[PyTango.DevDouble, PyTango.IMAGE, PyTango.READ, 10000000, 7 ]],
#        'ResultSize': [[PyTango.DevLong, PyTango.SCALAR, PyTango.READ ]],
        'automaticaoi': [[PyTango.DevBoolean, PyTango.SCALAR, PyTango.READ_WRITE ]],
        'intensity': [[PyTango.DevDouble, PyTango.SCALAR, PyTango.READ ]],
        'max_intensity': [[PyTango.DevDouble, PyTango.SCALAR, PyTango.READ]],
        'proj_x': [[PyTango.DevLong, PyTango.SPECTRUM, PyTango.READ, 2048 ]],
        'proj_y': [[PyTango.DevLong, PyTango.SPECTRUM, PyTango.READ, 2048 ]],
        'fwhm_x': [[PyTango.DevDouble, PyTango.SCALAR, PyTango.READ]],
        'fwhm_y': [[PyTango.DevDouble, PyTango.SCALAR, PyTango.READ]],
        'autoscale': [[PyTango.DevBoolean, PyTango.SCALAR, PyTango.READ_WRITE ]],
        'lut_method' : [[PyTango.DevString, PyTango.SCALAR, PyTango.READ_WRITE ]],
        'color_map': [[PyTango.DevBoolean, PyTango.SCALAR, PyTango.READ_WRITE ]],
        'bvdata':[[PyTango.DevEncoded, PyTango.SCALAR, PyTango.READ]],
        'calibration': [[PyTango.DevDouble, PyTango.SPECTRUM, PyTango.READ_WRITE, 2 ]],
        'beammark': [[PyTango.DevLong, PyTango.SPECTRUM, PyTango.READ_WRITE, 2 ]]
    }


#------------------------------------------------------------------
#    BpmDeviceServerClass Constructor
#------------------------------------------------------------------
    def __init__(self, name):
        PyTango.DeviceClass.__init__(self, name)
        self.set_type(name)

import threading
class BVDataTask(Core.Processlib.SinkTaskBase):
    Core.DEB_CLASS(Core.DebModApplication, "BVDataTask")

    class _PushingThread(threading.Thread):
        Core.DEB_CLASS(Core.DebModApplication, "_PushingThread")
        def __init__(self, task):
            threading.Thread.__init__(self)
            self._task = task
        def run(self):
            task = self._task
            #import pdb; pdb.set_trace()
            while task._stop is False:

                with task._lock:
                    while (task._data is None and
                           task._stop is False):
                        task._lock.wait()
                    if task._stop:
                        break
                    #local_stat = task._stat
                    #data = numpy.copy(task._data.buffer)
                    #data_frame = task._data.frameNumber
                    task._data = None
                    task._stat = None
                
                bvdata, bvdata_format = construct_bvdata(self._task._bpm_device)

                self._task._bpm_device.push_change_event("bvdata", bvdata_format, bvdata)
                
                
            
    def __init__(self, bpm_manager, bpm_device):
        Core.Processlib.SinkTaskBase.__init__(self)
        self._bpm_device = bpm_device
        self._bpm_manager = bpm_manager
        self._lock = threading.Condition()
        self._data = None
        self._stat = None
        self._stop = False
        self._pushing_event_thread = self._PushingThread(self)
        self._pushing_event_thread.start()

    #https://stackoverflow.com/questions/1481488/what-is-the-del-method-how-to-call-it?utm_medium=organic&utm_source=google_rich_qa&utm_campaign=google_rich_qa
    def __del__(self):
        self._stop=True
        self._pushing_event_thread.join()


    def process(self, data):
       # stat = self._bpm_device.get_bpm_result(data.frameNumber, data.timestamp)
        
        with self._lock:
            self._data = Core.Processlib.Data(data)
            #self._stat = stat
            #print "rx data",data.frameNumber,data.buffer.shape
            self._lock.notify()
            

def construct_bvdata(bpm):
    image = _control_ref().ReadImage() 
    last_acq_time, last_x, last_y, last_intensity, last_fwhm_x, last_fwhm_y, last_max_intensity, last_proj_x, last_proj_y = bpm.get_bpm_result(image.frameNumber, image.timestamp) 
    lima_roi = _control_ref().image().getRoi()
    roi_top_left = lima_roi.getTopLeft()
    roi_size = lima_roi.getSize()
    height, width = image.buffer.shape
    jpegFile = cStringIO.StringIO()
    if bpm.lut_method=="LINEAR":
        lut_method = pixmaptools.LUT.LINEAR
    else:
        lut_method = pixmaptools.LUT.LOG
    if bpm.color_map==True:
        color_map = pixmaptools.LUT.Palette.TEMP
    else:
        color_map = pixmaptools.LUT.Palette.GREYSCALE

    if bpm.autoscale:
        img_buffer = pixmaptools.LUT.transform_autoscale(image.buffer, bpm.palette[color_map], lut_method)[0]
    else:
        img_buffer = pixmaptools.LUT.transform(image.buffer, bpm.palette[color_map], lut_method, 0, 4*4096)[0]
    img_buffer.shape = (height, width, 4)
    I = Image.fromarray(img_buffer, "RGBX").convert("RGB")
    I.save(jpegFile, "jpeg", quality=95)
    raw_jpeg_data = jpegFile.getvalue()
    image_jpeg = base64.b64encode(raw_jpeg_data)
    profil_x = str(last_proj_x.tolist())
    profil_y = str(last_proj_y.tolist())
    bvdata_format='dldddliiiidd%ds%ds%ds' %(len(profil_x),len(profil_y),len(image_jpeg))
    print "SENT : ", last_acq_time, " FRAMENUMBER : ", image.frameNumber
    bvdata = struct.pack(
                bvdata_format,
                last_acq_time,
                image.frameNumber,
		        last_x,
		        last_y,
		        last_intensity,
		        last_max_intensity,
		        roi_top_left.x,
		        roi_top_left.y,
		        roi_size.getWidth(),
		        roi_size.getHeight(),
		        last_fwhm_x,
		        last_fwhm_y,
                profil_x,
                profil_y,
                image_jpeg)
    return bvdata, bvdata_format




_control_ref = None
def set_control_ref(control_class_ref) :
    global _control_ref
    _control_ref= control_class_ref

def get_tango_specific_class_n_device() :
   return BpmDeviceServerClass,BpmDeviceServer