#!/usr/bin/env python3

from time import sleep

from ev3dev2.motor import LargeMotor, MediumMotor, OUTPUT_A, OUTPUT_B, OUTPUT_C

from ev3dev2.sensor import INPUT_1, INPUT_2,INPUT_3
from ev3dev2.sensor.lego import TouchSensor, ColorSensor

lewy_motor = LargeMotor(OUTPUT_A)	#lewy
prawy_motor = LargeMotor(OUTPUT_B)	#prawy
m3 = MediumMotor(OUTPUT_C)

s1 = TouchSensor(INPUT_3)
prawy_sensor = ColorSensor(INPUT_2)	#prawy
lewy_sensor = ColorSensor(INPUT_1)	#lewy

sign = 1
speed = -5

while True:

#	if(prawy_sensor.color_name == "Black" and lewy_sensor.color_name == "Black"):
#		lewy_motor.on(sign*speed)
#		prawy_motor.on(sign*speed)
#		print('Going straight')
#		prev = [lewy_sensor.color_name,prawy_sensor.color_name]

	#Skręt w prawo
	elif(prawy_sensor.color_name == "Black" and lewy_sensor.color_name == "White"):
		lewy_motor.on(sign*speed)
		prawy_motor.on(0*speed)
		print('turning Rignt')
		prev = [lewy_sensor.color_name,prawy_sensor.color_name]

		if(lewy_sensor.color_name == "Black" and prawy_sensor.color_name == "White"):
			while()
				lewy_motor.on(0*speed)
				prawy_motor.on(sign*speed)
				print('turning Rignt')
				prev = [lewy_sensor.color_name,prawy_sensor.color_name]


	#Skręt w lewo
	elif(lewy_sensor.color_name == "Black" and prawy_sensor.color_name == "White"):
		lewy_motor.on(0*speed)
		prawy_motor.on(sign*speed)
		print('turning Left')
		prev = [lewy_sensor.color_name,prawy_sensor.color_name]
		
#		while True:
#			if(lewy_sensor.color_name == "White"):
#				lewy_motor.on(-sign*speed)
#				prawy_motor.on(0*speed)
#				prev = [lewy_sensor.color_name,prawy_sensor.color_name]
#
#			else:
#				break

	#Jazda prosto
	else:
		m1.on(-sign*speed)
		m2.on(-sign*speed)
		print('Go straight')
		
#	m1.on(sign*speed)
#	m2.on(-sign*speed)
#	m3.on(0*speed)
#	print('Button ' + ('pressed.' if s1.is_pressed else 'not pressed.'))
#	print('Color 1 ' + str(s2.rgb) + ' detected as ' + str(s2.color_name) + '.')
#	print('Color 2 ' + str(s3.rgb) + ' detected as ' + str(s3.color_name) + '.')
	sleep(0.01)

	if s1.is_pressed:
		sign = 0


