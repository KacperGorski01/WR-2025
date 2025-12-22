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

speed = 8  # Zwiększono lekko bazową prędkość dla płynności (można zmienić na 10)
intersection_time = 0.5
kp = 0.3
kd = 0.25
black_threshold = 15 # Poniżej tej wartości uznajemy, że sensor widzi "czarne" (skrzyżowanie)

# ================== FSM ==================

class Sterowanie:

    def __init__(self):
        self.stan = "Idle"
        self.czas_wejscia_stan = time.time()
        self.strona = "Puste"
        self.black_start = None
        self.touch_prev = False
        self.prev_error = 0  # <--- NAPRAWA: Inicjalizacja zmiennej dla członu D
        print("Naciśnij touch sensor! Stan: Idle")

    # ---------- ZMIANA STANU ----------
    def ustaw_stan(self, nowy):
        if self.stan != nowy:
            self.stan = nowy
            self.czas_wejscia_stan = time.time()
            self.stop() # Reset silników przy zmianie stanu
            print("-> Stan:", nowy)

    # ---------- AKCJE ----------
    
    def go_straight(self):
        m1.on(-speed)
        m2.on(-speed)

    def turn_left(self):
        self.strona = "L"

    def turn_right(self):
        self.strona = "R"

    def skrzyzowanie(self):
        # Jazda prosto z równą prędkością
        m1.on(-speed)
        m2.on(-speed)

    def wstecz(self):
        # Logika cofania przy wykryciu końca trasy/problemu
        if self.strona == "L":
            m1.on(speed)
            m2.on(-speed)
            time.sleep(1.5)
            print('korekcja L')
        elif self.strona == "R":
            m1.on(-speed)
            m2.on(speed)
            time.sleep(1.5)
            print('korekcja R')

    def stop(self):
        m1.off()
        m2.off()

    # ---------- FSM ----------
    def update(self):
        
        # Odczyt intensywności (0-100)
        L = s3.reflected_light_intensity
        R = s2.reflected_light_intensity

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
            
            # NOWA LOGIKA: Wykrywanie skrzyżowania 4-stronnego
            # Jeśli oba sensory widzą czarne (< 15), to jest to linia poprzeczna.
            # Natychmiast przechodzimy do stanu 'Skrzyzowanie', aby przejechać je na wprost.
            if L < black_threshold and R < black_threshold:
                self.ustaw_stan("Skrzyzowanie")
                return
            
            else:
                self.black_start = None
                
                # Algorytm PD (Proporcjonalno-Różniczkujący)
                error = L - R
                d_error = error - self.prev_error
                
                # Obliczamy korekcję skrętu
                turn = error * kp + kd * d_error
                self.prev_error = error
                
                # Aktualizacja zmiennej 'strona' (opcjonalne, dla logiki wstecz)
                if error < -5: self.strona = "L"
                elif error > 5: self.strona = "R"

                # Aplikacja mocy na silniki
                m1_speed = -speed - turn
                m2_speed = -speed + turn
                
                # Zabezpieczenie zakresu mocy (-100 do 100)
                m1_speed = max(min(m1_speed, 15), -15)
                m2_speed = max(min(m2_speed, 15), -15)
                
                m1.on(m1_speed)
                m2.on(m2_speed)

        # ===== SKRZYŻOWANIE =====
        elif self.stan == "Skrzyzowanie":
            self.skrzyzowanie()

            # NOWA LOGIKA WYJŚCIA:
            # 1. "Blind Time": Przez pierwsze 0.2 sekundy ignorujemy czujniki.
            #    Pozwala to robotowi wjechać na linię i zjechać z niej bez "paniki" algorytmu.
            if time.time() - self.czas_wejscia_stan < 0.2:
                return

            # 2. Po upływie czasu "ślepęgo", sprawdzamy czy wyjechaliśmy na białe.
            #    Jeśli którykolwiek sensor widzi jasno (> 40), uznajemy, że skrzyżowanie pokonane.
            if L > 40 or R > 40:
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
#    time.sleep(0.005)
