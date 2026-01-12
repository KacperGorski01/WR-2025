#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Transporter zgodnie ze sprawozdaniem:
- PID taki jak w line_follower, ale prędkość bazowa ~2x mniejsza
- zdarzenia:
  1) Pierwszy zjazd: zielony na prawym/lewym -> skręt w odpowiednią stronę + do przodu
  2) Podniesienie: IR < 20cm i robot "po zjeździe" -> do przodu ~80° koła, podniesienie, zawrót, do przodu
  3) Powrót na trasę po zabraniu: oba czarne -> skręt zgodny z poprzednim zjazdem
  4) Zjazd do opuszczenia: czerwony na prawym/lewym i blok podniesiony -> skręt
  5) Opuszczenie: oba czerwone po skręcie -> cofanie na środek, opuszczenie, cofnięcie, obrót 180
  6) Powrót na trasę po odłożeniu: oba czarne -> skręt i reset flag
"""

import time
from ev3dev2.motor import (
    LargeMotor, MediumMotor,
    OUTPUT_A, OUTPUT_B, OUTPUT_C,
    SpeedNativeUnits
)
from ev3dev2.sensor.lego import ColorSensor, InfraredSensor
from ev3dev2.sensor import INPUT_1, INPUT_2, INPUT_3
from ev3dev2.button import Button
from ev3dev2.sound import Sound


# === PORTY (zmień, jeśli potrzebujesz) ===
LEFT_MOTOR_PORT = OUTPUT_A
RIGHT_MOTOR_PORT = OUTPUT_B
LIFT_MOTOR_PORT = OUTPUT_C

LEFT_COLOR_PORT = INPUT_1
RIGHT_COLOR_PORT = INPUT_2
IR_PORT = INPUT_3

# === PID (jak w sprawozdaniu) ===
DT = 0.01
KP = 3.0
KI = 4.0
KD = 0.05


# Prędkość bazowa ~2x mniejsza niż w line_follower (wg sprawozdania)
def dynamic_base_speed_transport(error: float) -> int:
    e = abs(error)
    if e > 25:
        return -45
    elif e > 18:
        return -60
    elif e > 12:
        return -85
    else:
        return -125


# === Pomocnicze ruchy ===

def brake_all(lm: LargeMotor, rm: LargeMotor):
    lm.stop(stop_action='brake')
    rm.stop(stop_action='brake')


def drive_for_degrees(lm: LargeMotor, rm: LargeMotor, speed: int, degrees: int):
    """
    Jedzie prosto: oba silniki ten sam speed_sp, aż koło (silnik) zrobi 'degrees'.
    Ujemny speed = do przodu jeśli masz odwrotnie skonfigurowane (jak w sprawozdaniu).
    """
    lm.position = 0
    rm.position = 0
    lm.run_forever(speed_sp=speed)
    rm.run_forever(speed_sp=speed)
    target = abs(degrees)

    while abs(lm.position) < target and abs(rm.position) < target:
        time.sleep(0.005)
    brake_all(lm, rm)


def turn_in_place(lm: LargeMotor, rm: LargeMotor, speed: int, degrees: int, direction: str):
    """
    Obrót w miejscu: direction 'L' lub 'R'.
    degrees - przybliżone; zależy od konstrukcji.
    """
    lm.position = 0
    rm.position = 0

    if direction.upper() == 'L':
        lm.run_forever(speed_sp=+abs(speed))
        rm.run_forever(speed_sp=-abs(speed))
    else:
        lm.run_forever(speed_sp=-abs(speed))
        rm.run_forever(speed_sp=+abs(speed))

    target = abs(degrees)
    while abs(lm.position) < target and abs(rm.position) < target:
        time.sleep(0.005)
    brake_all(lm, rm)


def turn_from_line(lm: LargeMotor, rm: LargeMotor, direction: str):
    """
    Skręt ze ścieżki w prawo/lewo (zjazd).
    """
    # wartości do dostrojenia pod tor; daję sensowne startowe
    turn_in_place(lm, rm, speed=160, degrees=160, direction=direction)
    drive_for_degrees(lm, rm, speed=-120, degrees=120)  # "kawałek do przodu"


def uturn(lm: LargeMotor, rm: LargeMotor):
    """Zawrót ~180 stopni."""
    turn_in_place(lm, rm, speed=180, degrees=320, direction='L')


def lift_up(lift: MediumMotor):
    """
    Podniesienie widłów.
    U Ciebie jest przekładnia 1:56, więc ruch jest wolny i precyzyjny.
    Wartości stopni do dostrojenia.
    """
    lift.on_for_degrees(speed=25, degrees=30, brake=True, block=True)


def lift_down(lift: MediumMotor):
    """Opuszczenie widłów (stopnie do dostrojenia)."""
    lift.on_for_degrees(speed=25, degrees=-30, brake=True, block=True)


def main():
    btn = Button()
    spk = Sound()

    lm = LargeMotor(LEFT_MOTOR_PORT)
    rm = LargeMotor(RIGHT_MOTOR_PORT)
    lift = MediumMotor(LIFT_MOTOR_PORT)

    l_cl = ColorSensor(LEFT_COLOR_PORT)
    r_cl = ColorSensor(RIGHT_COLOR_PORT)

    l_cl.mode = 'COL-REFLECT'
    r_cl.mode = 'COL-REFLECT'
    # kolor do zdarzeń:
    l_cl_color_mode = 'COL-COLOR'
    r_cl_color_mode = 'COL-COLOR'

    print("Naciśnij DOWN aby START/STOP.")
    spk.beep()

    while not btn.down:
        time.sleep(0.01)
    while btn.down:
        time.sleep(0.01)

    # kalibracja białego (jak w sprawozdaniu; jeśli brak metody -> pominie)
    if hasattr(l_cl, "calibrate_white"):
        l_cl.calibrate_white()
    if hasattr(r_cl, "calibrate_white"):
        r_cl.calibrate_white()

    integral = 0.0
    previous_error = 0.0

    # === Flagi (wg opisu zdarzeń) ===
    did_first_turn = False          # czy robot zjechał po zielonym po ładunek
    first_turn_dir = None           # 'L' lub 'R'
    has_block = False               # czy klocek podniesiony
    did_drop_turn = False           # czy zjechał na czerwonym do strefy odkładania
    drop_turn_dir = None            # 'L' lub 'R'

    running = True
    spk.beep()

    try:
        while running:
            if btn.down:
                running = False
                break

            # --- Odczyty ---
            # światło do PID
            l_light = l_cl.reflected_light_intensity
            r_light = r_cl.reflected_light_intensity
            error = float(l_light - r_light)

            # dynamiczna prędkość (wolniej)
            base_speed = dynamic_base_speed_transport(error)

            # PID
            integral += error * DT
            if abs(error) < 3:
                integral = 0.0
            derivative = (error - previous_error) / DT
            previous_error = error
            turn = (KP * error) + (KI * integral) + (KD * derivative)

            # --- Kolory (zdarzenia) ---
            # Na chwilę przełączamy tryb na kolor, odczyt, wracamy na REFLECT.
            # To imituje "naprzemienne sprawdzanie koloru i natężenia" ze sprawozdania.
            l_cl.mode = l_cl_color_mode
            r_cl.mode = r_cl_color_mode
            l_col = l_cl.color   # 0..7
            r_col = r_cl.color
            l_cl.mode = 'COL-REFLECT'
            r_cl.mode = 'COL-REFLECT'

            # Mapowanie kolorów (ev3dev2):
            # 1=BLACK, 2=BLUE, 3=GREEN, 4=YELLOW, 5=RED, 6=WHITE, 7=BROWN
            BLACK = 1
            GREEN = 3
            RED = 5

            # --- ZDARZENIE 1: szukanie koloru
            if (not did_first_turn) and (not has_block):

                lift_up()
                time.sleep(10000)


            time.sleep(DT)

    finally:
        brake_all(lm, rm)
        lift.stop(stop_action='brake')
        spk.beep()
        print("STOP.")


if __name__ == "__main__":
    main()
