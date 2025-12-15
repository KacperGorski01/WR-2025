#!/usr/bin/env python3

import time
from time import sleep

from ev3dev2.motor import LargeMotor, MediumMotor, OUTPUT_A, OUTPUT_B, OUTPUT_C

from ev3dev2.sensor import INPUT_1, INPUT_2,INPUT_3
from ev3dev2.sensor.lego import TouchSensor, ColorSensor

m1 = LargeMotor(OUTPUT_A)	#lewy
m2 = LargeMotor(OUTPUT_B)	#prawy
m3 = MediumMotor(OUTPUT_C)

s1 = TouchSensor(INPUT_3)
s2 = ColorSensor(INPUT_2)	#prawy
s3 = ColorSensor(INPUT_1)	#lewy

speed = 5

class Sterowanie:
	sign = 1
	strona = 'Puste'
	def __init__(self):
		self.stan = 'Idle'
		self.czas_wejscia_stan = time.time()
		print("Nacisnij touch sensor! Aktualny stan: Idle")

	def ustaw_stan(self, nowy_stan):
		if(self.stan != nowy_stan):
			self.stan = nowy_stan
			self.czas_wejscia_stan = time.time()
	
	def go_straight(self):
		czas_trwania = time.time() - self.czas_wejscia_stan
		m1.on(-self.sign*speed)
		m2.on(-self.sign*speed)
		if(czas_trwania >= 2.0):
			m1.on(-self.sign*speed*2)
			m2.on(-self.sign*speed*2)

		print('Go straight')

	def turn_left(self):
		m1.on(self.sign*speed)
		m2.on(-self.sign*speed)
		self.strona = 'L'
		print('turning Left')

	def turn_right(self):
		m1.on(-self.sign*speed)
		m2.on(self.sign*speed)
		self.strona = 'R'
		print('turning Right')

	def skrzyzowanie(self):
		m1.on(-self.sign*speed)
		m2.on(-self.sign*speed)
		print('Go straight')

	def wstecz(self):
		if(self.strona == 'R'):
			m1.on(-self.sign*speed)
			m2.on(self.sign*speed)
			print('korekcja prawa')
			sleep(2)
		if(self.strona == 'L'):
			m1.on(self.sign*speed)
			m2.on(-self.sign*speed)
			print('korekcja lewa')
			sleep(2)
		print('idz wstecz')
#		if (self.strona == 'R'):
#			m1.on_for_degrees(power=self.sign * speed, degrees=-90, block=True)
#			m2.on_for_degrees(power=self.sign * speed, degrees=90, block=True)
#		if (self.strona == 'L'):
#			m1.on(self.sign*speed)
#			m2.on(-self.sign*speed)

	def wylaczenie(self):
		self.sign = 0

pojazd = Sterowanie()


while True:

	if(pojazd.stan == 'Idle' and s1.is_pressed):
		pojazd.state = pojazd.go_straight()

	elif(s2.color_name == "Black" and s3.color_name == "White"):
		pojazd.state = pojazd.turn_right()

	elif(s3.color_name == "Black" and s2.color_name == "White"):
		pojazd.state = pojazd.turn_left()

	elif(s3.color_name == "Black" and s2.color_name == "Black"):
		pojazd.state = pojazd.wstecz()
	

	elif(s1.is_pressed):
		pojazd.state = pojazd.wylaczenie()

	else:
		pojazd.state = pojazd.go_straight()



