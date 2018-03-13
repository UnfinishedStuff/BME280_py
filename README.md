# BME280_py
A python script for controlling a BME280 temperature, humidity and pressure sensor with the Raspberry Pi.  

STATUS:  Working, although see the KNOWN ISSUES section for a disclaimer.

This repo has three elements: BME280.py is the script which controls the sensor, weather.py is a very simple script showing you how you can use BME280.py, and README.md is this document which you are reading now.


Suggested use:
Place BME280.py in the same directory as your script.  At the top of your script type the line `import BME280`.
Where you want the readings use `temperature, pressure, humidity = BME280.get_single_reading()`.  This will create the variables `temperature`, `pressure`, and `humidity` and store the corresponding readings in those variables in degrees C, hPa and %RH respectively.
Print or process the readings as you see fit.

KNOWN ISSUES:

In the datasheet there are several methods for taking the raw readings and converting them to meaningful values. Currently these use the "complex" method for pressure and "simple" methods for temperature and humidity.  The BME280.py script includes a "simple" pressure method as well, however it was providing values which were significantly different to the "complex" method.  I really need to do a QA pass on these methods and check that they're implemented properly:  if your readings look off this is probably why.
