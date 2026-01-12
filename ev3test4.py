#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Linefollower (PID) zgodnie ze sprawozdaniem:
- 2 czujniki światła/koloru, praca na reflected light intensity
- kalibracja na białej planszy (calibrate_white)
- PID na różnicy: error = left - right
- dynamiczna regulacja bazowej prędkości zależnie od |error|
- zerowanie całki gdy |error| < 3
- start/stop przyciskiem EV3
"""

import time
from ev3dev2.motor import LargeMotor, OUTPUT_B, OUTPUT_A, SpeedNativeUnits, MediumMotor
from ev3dev2.sensor.lego import ColorSensor
from ev3dev2.sensor import INPUT_1, INPUT_2
from ev3dev2.button import Button
from ev3dev2.sound import Sound


# === PORTY (zmień, jeśli potrzebujesz) ===
LEFT_MOTOR_PORT = OUTPUT_A
RIGHT_MOTOR_PORT = OUTPUT_B
LEFT_COLOR_PORT = INPUT_1
RIGHT_COLOR_PORT = INPUT_2

# === PID wg sprawozdania ===
DT = 0.01
KP = 3
KI = 4.0
KD = 0.05


def dynamic_base_speed(error: float) -> int:
    """Dynamiczna prędkość bazowa wg progów ze sprawozdania."""
    e = abs(error)
    if e > 25:
        return -50
    elif e > 15:
        return -100
    elif e > 10:
        return -200
    else:
        return -1000


def main():
    btn = Button()
    spk = Sound()

    l_motor = LargeMotor(LEFT_MOTOR_PORT)
    r_motor = LargeMotor(RIGHT_MOTOR_PORT)

    l_cl = ColorSensor(LEFT_COLOR_PORT)
    r_cl = ColorSensor(RIGHT_COLOR_PORT)

    # reflected_light_intensity działa w trybie odbitego światła
    l_cl.mode = 'COL-REFLECT'
    r_cl.mode = 'COL-REFLECT'

    print("Naciśnij DOWN aby START/STOP.")
    spk.beep()

    # czekaj na start
    while not btn.down:
        time.sleep(0.01)
    while btn.down:
        time.sleep(0.01)

    # kalibracja na białej planszy (wg sprawozdania)
    # UWAGA: w zależności od wersji biblioteki, calibrate_white może nie istnieć.
    # Jeśli u Ciebie go brak, zakomentuj i zostaw samą pracę na reflected_light_intensity.
    if hasattr(l_cl, "calibrate_white"):
        l_cl.calibrate_white()
    if hasattr(r_cl, "calibrate_white"):
        r_cl.calibrate_white()

    integral = 0.0
    previous_error = 0.0

    running = True
    spk.beep()

    try:
        while running:
            # stop przyciskiem
            if btn.down:
                running = False
                break

            l_light = l_cl.reflected_light_intensity
            r_light = r_cl.reflected_light_intensity
                
            # === Standardowa logika PID (jeśli nie skrzyżowanie) ===
            error = float(l_light - r_light)

            # całka + zerowanie wg sprawozdania
            integral += error * DT
            if abs(error) < 3:
                integral = 0.0

            derivative = (error - previous_error) / DT
            previous_error = error

            turn = (KP * error) + (KI * integral) + (KD * derivative)

            speed = dynamic_base_speed(error)

            # sterowanie jak w sprawozdaniu:
            # l = speed - turn
            # r = speed + turn
            sp1 = speed - turn
            sp2 = speed + turn

            # === Limity prędkości i sterowanie silnikami (wspólne) ===
            if sp1 > 1050:
                sp1 = 1050
        
            if sp2 > 1050:
                sp2 = 1050

            if sp1 < -1050:
                sp1 = -1050
        
            if sp2 < -1050:
                sp2 = -1050

            l_motor.run_forever(speed_sp = sp1)
            r_motor.run_forever(speed_sp = sp2)

            time.sleep(DT)

    finally:
        l_motor.stop(stop_action='brake')
        r_motor.stop(stop_action='brake')
        spk.beep()
        print("STOP.")


if __name__ == "__main__":
    main()