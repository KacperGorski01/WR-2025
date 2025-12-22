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

speed = 20  # Zwiększono lekko bazową prędkość dla płynności (można zmienić na 10)
intersection_time = 0.5
kp = 0.4    # Współczynnik wzmocnienia dla ruchów korygujących (Gain)
black_threshold = 15 # Poniżej tej wartości uznajemy, że sensor widzi "czarne" (skrzyżowanie)

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
            self.stop() # Reset silników przy zmianie stanu
            print("-> Stan:", nowy)

    # ---------- AKCJE ----------
    # Zmieniono logikę metod ruchu, aby wspierały płynną korekcję
    # W nowym podejściu sterujemy silnikami bezpośrednio w update(),
    # ale zachowujemy metody dla kompatybilności struktury.

    def go_straight(self):
        m1.on(-speed)
        m2.on(-speed)

    def turn_left(self):
        # Metoda pomocnicza - w trybie proporcjonalnym sterowanie jest w update
        self.strona = "L"

    def turn_right(self):
        # Metoda pomocnicza
        self.strona = "R"

    def skrzyzowanie(self):
        m1.on(-speed)
        m2.on(-speed)

    def wstecz(self):
        # Logika cofania przy wykryciu końca trasy/problemu
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
        
        # ZMIANA 1: Odczyt intensywności (0-100) zamiast nazwy koloru
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
            
            # ZMIANA 2: Wykrywanie skrzyżowania na bazie progu (threshold)
            # Jeśli oba czujniki widzą bardzo ciemno (< 15)
            if L < black_threshold and R < black_threshold:
                if self.black_start is None:
                    self.black_start = time.time()
                    self.wstecz() # Zachowanie ze starego kodu
                elif time.time() - self.black_start > intersection_time:
                    self.ustaw_stan("Skrzyzowanie")
                    return
            
            else:
                self.black_start = None
                
                # ZMIANA 3: Algorytm Proporcjonalny (P-Control)
                # Obliczamy błąd: różnica jasności między lewym a prawym sensorem
                error = L - R
                
                # Obliczamy korekcję skrętu
                turn = error * kp
                
                # Aktualizacja zmiennej 'strona' dla logiki 'wstecz'
                if error < -5: self.turn_left()  # L ciemniejsze -> skręt w lewo
                elif error > 5: self.turn_right() # R ciemniejsze -> skręt w prawo
                else: self.strona = "Puste"

                # Aplikacja mocy na silniki (uwaga: w oryginalnym kodzie '-' to przód)
                # Jeśli turn dodatni (L > R), robot skręca w prawo (lewy szybciej, prawy wolniej)
                # Jeśli turn ujemny (L < R), robot skręca w lewo
                
                m1_speed = -speed - turn
                m2_speed = -speed + turn
                
                # Zabezpieczenie zakresu mocy (-100 do 100)
                m1_speed = max(min(m1_speed, 100), -100)
                m2_speed = max(min(m2_speed, 100), -100)
                
                m1.on(m1_speed)
                m2.on(m2_speed)


        # ===== SKRZYŻOWANIE =====
        elif self.stan == "Skrzyzowanie":
            self.skrzyzowanie()

            # Wyjście ze skrzyżowania, gdy oba zobaczą jasno (np. > 40)
            if L > 40 and R > 40:
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
    # Zmniejszono sleep dla szybszej reakcji pętli sterowania
    time.sleep(0.005)
