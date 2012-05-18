import time
import serial
import optparse
import multiprocessing

class Memsic2125(multiprocessing.Process):
  """ Starts a separate thread to read accelerometer data from the serial port
  """

  x_acceleration = multiprocessing.Value('f',0)
  y_acceleration = multiprocessing.Value('f',0)

  filename = multiprocessing.Queue()
  file = None

  start_recording_flag = multiprocessing.Event()
  stop_recording_flag = multiprocessing.Event()
  recording_flag = multiprocessing.Event()

  x_offset = 10000
  y_offset = 10000
  
  def __init__(self, port):
    self.serial = serial.Serial(port, 57600)

    multiprocessing.Process.__init__(self, target=self.run)

  def run(self):
    while True:
      # First, check if we should start recording to file
      if self.start_recording_flag.is_set():
        self.file = open(self.filename.get(),'w')
        self.recording_flag.set()
        self.start_recording_flag.clear()

      if self.stop_recording_flag.is_set():
        self.file = None
        self.recording_flag.clear()
        self.stop_recording_flag.clear()

      # Sometimes we might get some garbage, so just ignore it.
      try:
        new_x, new_y = self.serial.readline().split(',')

        #corrected_x = (float(new_x)/self.x_offset - .5)*self.max_g
        #corrected_y = (float(new_y)/self.y_offset - .5)*self.max_g
        corrected_x = (float(new_x)/self.x_offset - .5)/.125
        corrected_y = (float(new_y)/self.y_offset - .5)/.125

        self.x_acceleration.value = corrected_x
        self.y_acceleration.value = corrected_y

        if self.file != None:
          time_string = time.strftime("%y/%m/%d, %H:%M", time.localtime(time.time()))
          self.file.write('%s, %s,%s\n'%(time_string, corrected_x, corrected_y))
          self.file.flush()

      except ValueError as e:
        pass

  def StartCaptureToFile(self, filename):
    self.filename.put(filename)
    self.start_recording_flag.set()

  def StopCaptureToFile(self):
    self.stop_recording_flag.set()

  def GetAcceleration(self):
    return self.x_acceleration.value, self.y_acceleration.value


if __name__ == "__main__":
  # Log to the screen and an optional file

  parser = optparse.OptionParser()
  parser.add_option("-p", "--serialport", dest="serialportname",
                    help="serial port (ex: /dev/ttyusb0)", default="/dev/ttyacm0")
  parser.add_option("-f", "--filename", dest="filename",
                    help="filename", default="")
  (options, args) = parser.parse_args()

  m = Memsic2125(options.serialportname)
  m.start()

  if options.filename != '':
    m.StartCaptureToFile(options.filename)

  
  max_y_acc = 0
  min_y_acc = 100000

  max_x_acc = 0
  min_x_acc = 100000
  while True:
    x_acc, y_acc = m.GetAcceleration()
    # filter garbage?
    if x_acc < -3 or y_acc < -3:
      pass

    else:
    # if we aren't saving to file, dump to console
      min_x_acc = min(min_x_acc, x_acc)
      max_x_acc = max(max_x_acc, x_acc)
      min_y_acc = min(min_y_acc, y_acc)
      max_y_acc = max(max_y_acc, y_acc)
     
      print '%06.5f %06.5f %06.5f %06.5f %06.5f %06.5f'%(
        x_acc, min_x_acc, max_x_acc,
        y_acc, min_y_acc, max_y_acc
      )

