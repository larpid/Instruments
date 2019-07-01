from spinpluspython.Instruments.PySerial_by_Jairo_Moldes import PySerial
import sys
from serial.tools import port_info

class PySerial_pimped(PySerial.PySerial):

	# ------------------------------------------------------------------
	#	Write Port attribute
	# ----------------------------+--------------------------------------
	def write_Port(self, serial_number):
		"""pimped write_Port attribute to get port by devices S/N number aquired from *IDN? call"""
		self.info_stream("In %s::write_Port()" % self.get_name())

		#	Add your own code here
		for port in port_info.comports():


		self.port =
		self.configure = True





if __name__ == "__main__":
	PySerial.main(sys.argv)
