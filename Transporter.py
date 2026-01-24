#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
from ev3dev2.motor import LargeMotor, MediumMotor, OUTPUT_A, OUTPUT_B, OUTPUT_C
from ev3dev2.sensor.lego import ColorSensor
from ev3dev2.sensor import INPUT_1, INPUT_2
from ev3dev2.button import Button
from ev3dev2.sound import Sound

# ===== KONFIGURACJA =====
LEFT_MOTOR_PORT = OUTPUT_A
RIGHT_MOTOR_PORT = OUTPUT_B
LIFT_MOTOR_PORT = OUTPUT_C
LEFT_COLOR_PORT = INPUT_1
RIGHT_COLOR_PORT = INPUT_2

# PID
DT = 0.01
KP, KI, KD = 0.8, 3.0, 0.02

# KOLORY EV3
BLACK, BLUE, GREEN, YELLOW, RED, WHITE = 1, 2, 3, 4, 5, 6

# STANY
FOLLOW_LINE, TURN_TO_PACKAGE, GO_TO_PACKAGE = 0, 1, 2
PACKAGE_RETURN, GO_TO_GOAL, TURN_TO_PACKAGE_2 = 3, 4, 5
GO_TO_PACKAGE_2 = 6

# INICJALIZACJA URZĄDZEŃ
l_motor = LargeMotor(LEFT_MOTOR_PORT)
r_motor = LargeMotor(RIGHT_MOTOR_PORT)
lift = MediumMotor(LIFT_MOTOR_PORT)
l_cl = ColorSensor(LEFT_COLOR_PORT)
r_cl = ColorSensor(RIGHT_COLOR_PORT)
btn = Button()
spk = Sound()

# ===== FUNKCJE POMOCNICZE =====

def dynamic_base_speed(error):
    e = abs(error)
    if e > 25: return -15
    elif e > 15: return -30
    elif e > 10: return -50
    else: return -80

def brake():
    l_motor.stop(stop_action='brake')
    r_motor.stop(stop_action='brake')

def turn_90_left():
    l_motor.run_to_rel_pos(speed_sp=150, position_sp=300, stop_action='brake') # Przykładowe stopnie
    r_motor.run_to_rel_pos(speed_sp=-150, position_sp=-300, stop_action='brake')
    time.sleep(1.1)

def turn_90_right():
    l_motor.run_forever(speed_sp=-150)
    r_motor.run_forever(speed_sp=150)
    time.sleep(1.1)
    brake()

def turn_180():
    l_motor.run_forever(speed_sp=150)
    r_motor.run_forever(speed_sp=-150)
    time.sleep(2)
    brake()

def forward(time_s, speed=-150):
    l_motor.run_forever(speed_sp=speed)
    r_motor.run_forever(speed_sp=speed)
    time.sleep(time_s)
    brake()

# ===== MAIN =====

def main():
    spk.beep()
    print("WAITING FOR DOWN BUTTON...")
    while not btn.down: time.sleep(0.01)
    while btn.down: time.sleep(0.01)

    l_cl.mode = 'COL-REFLECT'
    r_cl.mode = 'COL-REFLECT'

    integral = 0
    prev_error = 0
    direction = None
    state = FOLLOW_LINE
    green_start_time = None

    while True:
        if btn.down: # Wyjście awaryjne
            break

        # Szybki odczyt kolorów do logiki stanów
        l_cl.mode = 'COL-COLOR'
        r_cl.mode = 'COL-COLOR'
        l_col = l_cl.color
        r_col = r_cl.color
        
        # Powrót do odbicia dla PID
        l_cl.mode = 'COL-REFLECT'
        r_cl.mode = 'COL-REFLECT'
        l_light = l_cl.reflected_light_intensity
        r_light = r_cl.reflected_light_intensity

        # --- LOGIKA STANÓW ---
        if state == FOLLOW_LINE:
            if l_col == YELLOW:
                brake()
                direction = "L"
                state = TURN_TO_PACKAGE
            elif r_col == YELLOW:
                brake()
                direction = "R"
                state = TURN_TO_PACKAGE
            # Jeśli nie wykryto żółtego, PID jedzie dalej (na końcu pętli)

        elif state == TURN_TO_PACKAGE:
            if direction == 'L':
                forward(1.0)
                turn_90_left()
                forward(1.5)
            else:
                forward(1.0)
                turn_90_right()
                forward(1.5)
            state = GO_TO_PACKAGE

        elif state == GO_TO_PACKAGE:
            if l_col == YELLOW or r_col == YELLOW:
                brake()
                forward(0.25) 
                lift.on_for_degrees(speed=25, degrees=450, brake=True, block=True)
                state = PACKAGE_RETURN

        elif state == PACKAGE_RETURN:
            turn_180()
            forward(0.4)
            state = GO_TO_GOAL

        elif state == GO_TO_GOAL:
            if l_col == YELLOW or r_col == YELLOW:
                if green_start_time is None:
                    green_start_time = time.time()
                elif time.time() - green_start_time >= 0.5:
                    brake()
                    state = TURN_TO_PACKAGE_2
            else:
                green_start_time = None

        elif state == TURN_TO_PACKAGE_2:
            forward(0.1)
            turn_90_left()
            forward(0.4)
            state = GO_TO_PACKAGE_2

        elif state == GO_TO_PACKAGE_2:
            if l_col == YELLOW or r_col == YELLOW:
                brake()
                forward(0.25)
                lift.on_for_degrees(speed=25, degrees=-450, brake=True, block=True)
                state = FOLLOW_LINE # Lub zakończenie programu

        # --- OBLICZENIA PID (Wspólne dla stanów "ruchowych") ---
        # PID działa w stanach FOLLOW_LINE, GO_TO_PACKAGE, GO_TO_GOAL, GO_TO_PACKAGE_2
        if state in [FOLLOW_LINE, GO_TO_PACKAGE, GO_TO_GOAL, GO_TO_PACKAGE_2]:
            error = float(l_light - r_light)
            integral += error * DT
            if abs(error) < 3: integral = 0
            
            derivative = (error - prev_error) / DT
            prev_error = error

            turn_val = KP * error + KI * integral + KD * derivative
            speed = dynamic_base_speed(error)

            l_motor.run_forever(speed_sp=max(min(speed - turn_val, 1000), -1000))
            r_motor.run_forever(speed_sp=max(min(speed + turn_val, 1000), -1000))

        time.sleep(DT)

    brake()
    spk.beep()
    print("STOP")

if __name__ == "__main__":
    main()