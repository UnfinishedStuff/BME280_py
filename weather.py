############################################
#An example script showing how to use the BME280.py script
#for reading BME280 sensors.
###########################################

import BME280
import time

try:
        while True:
                #Get the temperature, pressure and humidity values and assign
		#them variables called temperature, pressure and 
		#humidity respectively
                temperature, pressure, humidity = BME280.get_single_reading()
                #Format them to 2 decimal places and print them with units.
                print("Temperature = " + str("{:.2f}".format(temperature))\
 + "*C")
                print("Pressure    = " + str("{:.2f}".format(pressure))\
 + " hPa")
                print("Humidity    = " + str("{:.2f}".format(humidity))\
 + " %rH")
		print("")
		#Pause before the next set of readings are done
                time.sleep(1)
except KeyboardInterrupt:
        print("Manually stopped")
