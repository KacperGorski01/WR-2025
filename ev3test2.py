#!/usr/bin/env python3
import time

from ev3dev2.motor import LargeMotor, MediumMotor, OUTPUT_A, OUTPUT_B, OUTPUT_C
from ev3dev2.sensor import INPUT_1, INPUT_2, INPUT_3
from ev3dev2.sensor.lego import TouchSensor, ColorSensor

# ================== SILNIKI ==================

m1 = LargeMotor(OUTPUT_A)   # lewy
m2 = LargeMotor(OUTPUT_B)   # prawy
m3 = MediumMotor(OUTPUT_C)

# ================== CZUJNIKI ==================

s1 = TouchSensor(INPUT_3)
s2 = ColorSensor(INPUT_2)   # prawy
s3 = ColorSensor(INPUT_1)   # lewy

# ================== PARAMETRY ==================

speed = 10
intersection_time = 0.5

# ================== FSM ==================

class Sterowanie:

    def __init__(self):
        self.stan = "Idle"
        self.czas_wejscia_stan = time.time()
        self.strona = "Puste"
        self.black_start = None
        self.touch_prev = False
        print("Naciśnij touch sensor! Stan: Idle")

    # ---------- ZMIANA STANU ----------
    def ustaw_stan(self, nowy):
        if self.stan != nowy:
            self.stan = nowy
            self.czas_wejscia_stan = time.time()
            print("-> Stan:", nowy)

    # ---------- AKCJE ----------
    def go_straight(self):
        m1.on(-speed)
        m2.on(-speed)

    def turn_left(self):
        m1.on(speed)
        m2.on(-speed)
        self.strona = "L"

    def turn_right(self):
        m1.on(-speed)
        m2.on(speed)
        self.strona = "R"

    def skrzyzowanie(self):
        m1.on(-speed)
        m2.on(-speed)

    def wstecz(self):
        if self.strona == "L":
            m1.on(speed)
            m2.on(-speed)
            time.sleep(1)
            print('korekcja L')
        elif self.strona == "R":
            m1.on(-speed)
            m2.on(speed)
            time.sleep(1)
            print('korekcja R')

    def stop(self):
        m1.off()
        m2.off()

    # ---------- FSM ----------
    def update(self):

        L = s3.color_name
        R = s2.color_name

        # --- touch jako ZDARZENIE ---
        touch_now = s1.is_pressed
        touch_rising = touch_now and not self.touch_prev
        self.touch_prev = touch_now

        # ===== IDLE =====
        if self.stan == "Idle":
            self.stop()
            if touch_rising:
                self.ustaw_stan("Follow")
                return

        # ===== FOLLOW =====
        elif self.stan == "Follow":

            if L == "White" and R == "White":
                self.go_straight()
                self.black_start = None

            elif L == "Black" and R == "White":
                self.turn_left()
                self.black_start = None

            elif L == "White" and R == "Black":
                self.turn_right()
                self.black_start = None

            elif L == "Black" and R == "Black":
                if self.black_start is None:
                    self.black_start = time.time()
                    self.wstecz()
                elif time.time() - self.black_start > intersection_time:
                    self.ustaw_stan("Skrzyzowanie")
                    return
                

        # ===== SKRZYŻOWANIE =====
        elif self.stan == "Skrzyzowanie":
            self.skrzyzowanie()

            if L == "White" and R == "White":
                self.black_start = None
                self.ustaw_stan("Follow")
                return

        # ===== STOP =====
        if touch_rising and self.stan != "Idle":
            self.ustaw_stan("Idle")
            return


# ================== MAIN ==================

pojazd = Sterowanie()

while True:
    pojazd.update()
    time.sleep(0.01)
