from smbus import SMBus
import time
#Set bus to be the default way of interacting with SMBus(1)
bus = SMBus(1)

#Get the chip ID.  BME280 = 0x60
def get_id():
	bus.write_byte(0x76, 0xD0)
	id = bus.read_byte(0x76)
	return(id)

#Reset the device
def reset():
	#reset_value = [0xE0, 0xB6]
	bus.write_block_data(0x76,0xE0, [0xB6])

#Test read of default values
def test_read():
#	bus.write_byte(0x76, 0xD0)
	data = bus.read_i2c_block_data(0x76, 0xD0, 1)
	#data = bus.read_byte(0x76)
	print(data)

#Read the data
def get_single_reading():

	trim_consts = get_trim_consts()

	#Setup as 2x oversampling for pres/temp/hum, no IIR filter,
	# in FORCED mode (wake for single reading)
	bus.write_i2c_block_data(0x76, 0xF2, [0x02, 0xF4, 0x49])

	#Read the register containing the 8 bytes of pressure
	#/temperature/humidity data
	get_data_read = bus.read_i2c_block_data(0x76, 0xF7, 8)
	#Pass the 8 bytes of data into a list called data
	data = list(get_data_read)

	#Take the 3 bytes of pressure data, compute to single integer called
	# raw_pressure
	raw_pressure = (data[0] << 12) + (data[1] << 4) + (data[2] >> 4)
	#Take the 3 bytes of temp data, compute to single integer called
	# raw_temperature
	raw_temperature = (data[3] << 12) + (data[4] << 4) + (data[5] >> 4)
	#Take the two bytes of humidity data, compute to single integer called
	# raw_humidity
	raw_humidity = (data[6] << 8) + data[7]

	tfine, temperature = complex_temperature(raw_temperature, trim_consts)
	pressure = complex_pressure(tfine, raw_pressure, trim_consts)
	pressure = simple_pressure(tfine, raw_pressure, trim_consts)
	humidity = simple_humidity(tfine, raw_humidity, trim_consts)
	return(temperature, pressure, humidity)

#Calculate the temperature using the "complex" method in the datasheet
def complex_temperature(raw_temperature, trim_consts):
	t_var1 = ((((raw_temperature>>3) - (trim_consts['t1']<<1))) *\
 (trim_consts['t2'])) >> 11
	t_var2 = (((((raw_temperature>>4) - (trim_consts['t1'])) *\
	 ((raw_temperature>>4) - (trim_consts['t1'])))>>12)*\
(trim_consts['t3']))>>14
	tfine = t_var1 + t_var2
	temperature = ((tfine * 5 + 128) >> 8)/100.0
	return(tfine, temperature)

#Calculate the pressure using the "complex" method in the datasheet
def complex_pressure(tfine, raw_pressure, trim_consts):
	pvar1 = tfine - 12800
	pvar2 = pvar1 * pvar1 * trim_consts['p6']
	pvar2 = pvar2 + ((pvar1 * trim_consts['p5']) << 17)
	pvar2 = pvar2 + (trim_consts['p4'] << 35)
	pvar1 = ((pvar1 * pvar1 * trim_consts['p3']) >> 8) +\
 ((pvar1 * trim_consts['p2']) << 12)
	pvar1 = ((1 << 47) + pvar1) * trim_consts['p1'] >> 33

	if pvar1 == 0:
		pressure = 0
	else:
		pfine = 1048576 - raw_pressure
		pfine = (((pfine << 31) - pvar2) * 3125) / pvar1
		pvar1 = (trim_consts['p9'] * (pfine >> 13) * (pfine >> 13))\
 >> 25
		pvar2 = (trim_consts['p8'] * pfine) >> 19
		pressure = ((pfine + pvar1 + pvar2) >> 8) + (trim_consts['p7']\
 << 4)

	pressure = pressure / 256.0 / 100.0
	return(pressure)

#Calculate pressure using the "simple" method in the datasheet
def simple_pressure(tfine, raw_pressure, trim_consts):
        p_var1 = tfine/2.0 - 64000.0
	p_var2 = p_var1 * p_var1 * trim_consts['p6'] / 32768.0
	p_var2 = p_var2 + p_var1 * trim_consts['p5'] * 2.0
	p_var2 = p_var2 / 4.0 + trim_consts['p4'] * 65536.0
	p_var1 = (trim_consts['p3'] * p_var1 * p_var1 / 524288.0 +\
 trim_consts['p2'] * p_var1) / 524288.0
	p_var1 = (1.0 + p_var1 / 32768.0) * trim_consts['p1']

	if (p_var1 == 0):
		pressure = 0
	else:
		pfine = 1048576.0 - raw_pressure
		pfine = ((pfine - p_var2 / 4096.0) * 6250.0) / p_var1
		p_var1 = trim_consts['p9'] * pfine * pfine / 2147483648.0
		p_var2 = pfine * trim_consts['p8'] / 32768.0
		pressure = pfine + (p_var1 + p_var2 + trim_consts['p7'])\
 / 16.0

	pressure = pressure / 100.0
	return(pressure)

#Calculate humidity using the "simple" method in the datasheet
def simple_humidity(tfine, raw_humidity, trim_consts):
	var_h = tfine - 76800.0
	var_h = (raw_humidity - (trim_consts['h4'] * 64.0 + trim_consts['h5']\
 / 16384.0 * var_h)) * (trim_consts['h2'] / 65536.0 * (1.0 + trim_consts['h6']\
 / 67108864.0 * var_h * (1.0 + trim_consts['h3'] / 67108864.0 * var_h)))
	humidity = var_h * (1.0 - trim_consts['h1'] * var_h / 524288.0)

	if (humidity > 100.0):
		humidity = 100.0
	elif (humidity < 0.0):
		humidity = 0.0

	return(humidity)


#Get the trim constants for calculating presure/temperature/humidity
def get_trim_consts():
	#Get the raw bytes for temperature and pressure constants, put into
	# a list called "data"
	data = bus.read_i2c_block_data(0x76, 0x88, 24)

	#Calculate the temperature constants
	t1 = (data[1] << 8) | data[0]
	t2 = (data[3] << 8) | data[2]
	t3 = (data[5] << 8) | data[4]

	#Calculate the pressure constants
	p1 = (data[7] << 8) | data[6]
	p2 = (data[9] << 8) | data[8]
	p3 = (data[11] << 8) | data[10]
	p4 = (data[13] << 8) | data[12]
	p5 = (data[15] << 8) | data[14]
	p6 = (data[17] << 8) | data[16]
	p7 = (data[19] << 8) | data[18]
	p8 = (data[21] << 8) | data[20]
	p9 = (data[23] << 8) | data[22]

	#Get and process the humidity constants
	#Get the first constant byte, put it into a list called h1
	h1 = bus.read_byte_data(0x76, 0xA1)

	#Get the second set of bytes for the constants, put into a list
	# called get_hum_read
	# (WHY ARE THESE NOT IN CONTIGUOUS REGISTERS?!?!??!?!??!??!??!?!??!??!)
	hum = bus.read_i2c_block_data(0x76, 0xE1, 7)

	#Calculate the humidity constants

	h2 = (hum[1] << 8) | hum[0]
	h3 = hum[2]
	h4 = (hum[3] << 4) | (hum[4] & 0b00001111)
	h5 = (hum[4] >> 4) | (hum[5] << 4)
	h6 = hum[6]

	#Put all of the constants into a single list ("processed_data"),
	# px = pressure constant,
	#tx = temperature constant, hx = humidity constant
	processed_data = {'t1':t1, 't2':t2, 't3':t3, 'p1':p1, 'p2':p2,\
'p3':p3, 'p4':p4,'p5':p5, 'p6':p6, 'p7':p7, 'p8':p8, 'p9':p9, 'h1':h1,\
 'h2':h2,'h3':h3, 'h4':h4, 'h5':h5, 'h6':h6}

	#Check only signed constants to see if they're negative
	# (as per twos complement)
	for key,value in processed_data.items():
		if (key !=('p1' or 't1' or 'h1' or 'h3')) and\
 (value & (1 << 15)) !=0:
			#If they're negative, calculate that from the signed
			# byte
			value = value - (1 << 16)
			processed_data[key] = value

	#Return the final processed constants
	return processed_data

