import tkinter as tk
import RPi.GPIO as GPIO
from threading import Thread
import time

# GPIO Setup
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

motor_pins = [
    {'step': 27, 'direction': 21, 'enable': 4},
    {'step': 26, 'direction': 23, 'enable': 13},
    {'step': 12, 'direction': 20, 'enable': 22},
    {'step': 24, 'direction': 25, 'enable': 19},
    {'step': 16, 'direction': 6, 'enable': 5},
    {'step': 17, 'direction': 18, 'enable': 10}
]

motor_speed = [100, 100, 100, 100, 100, 100]
motor_threads = [None] * len(motor_pins)
speed_sliders = []

motor_direction = [GPIO.HIGH] * len(motor_pins)

for pin_set in motor_pins:
    for pin in pin_set.values():
        GPIO.setup(pin, GPIO.OUT)
        GPIO.output(pin, GPIO.LOW)

motor_on_duration = 0.5
motor_off_duration = 0.5
ramp_up_time = 0.3  # Initial ramp-up time set to 0.1 seconds

def start_motor(index):
    global motor_threads
    if motor_threads[index] is None or not motor_threads[index].is_alive():
        motor_threads[index] = Thread(target=run_motor, args=(index,))
        motor_threads[index].start()

def stop_motor(index):
    GPIO.output(motor_pins[index]['enable'], GPIO.HIGH)
    if motor_threads[index] is not None:
        motor_threads[index].join()
        motor_threads[index] = None

def stop_all_motors():
    for index in range(len(motor_pins)):
        GPIO.output(motor_pins[index]['enable'], GPIO.HIGH)
        if motor_threads[index] is not None:
            motor_threads[index].join()
            motor_threads[index] = None

def quit_program():
    stop_all_motors()
    root.destroy()

def run_motor(index):
    step_pin = motor_pins[index]['step']
    dir_pin = motor_pins[index]['direction']
    en_pin = motor_pins[index]['enable']

    GPIO.output(en_pin, GPIO.LOW)
    GPIO.output(dir_pin, motor_direction[index])

    while GPIO.input(en_pin) == GPIO.LOW:
        # Calculate the number of steps for ramp-up based on the ramp-up time and motor_on_duration
        total_steps = motor_on_duration / (1.0 / motor_speed[index])
        ramp_steps = ramp_up_time / (1.0 / motor_speed[index])
        current_speed = 1  # Start with a low speed
        speed_increment = (motor_speed[index] - current_speed) / ramp_steps

        # Ramp-up logic
        for step in range(int(total_steps)):
            if step < ramp_steps:
                current_speed += speed_increment
            GPIO.output(step_pin, GPIO.HIGH)
            time.sleep(1.0 / current_speed / 2)
            GPIO.output(step_pin, GPIO.LOW)
            time.sleep(1.0 / current_speed / 2)

        # Stop the motor for the specified off duration
        time.sleep(motor_off_duration)

def toggle_direction(index):
    if motor_direction[index] == GPIO.HIGH:
        motor_direction[index] = GPIO.LOW
    else:
        motor_direction[index] = GPIO.HIGH

    if motor_threads[index] is not None and motor_threads[index].is_alive():
        GPIO.output(motor_pins[index]['direction'], motor_direction[index])

def create_motor_control(page, motor_index, row):
    motor_frame = tk.Frame(page, bg='black')
    motor_frame.grid(row=row, column=0, padx=0, pady=0)

    def update_speed(index, value):
        motor_speed[index] = int(value)
        if motor_threads[index] is not None and motor_threads[index].is_alive():
            stop_motor(index)
            start_motor(index)

    start_button = tk.Button(motor_frame, text=f"Start \nMotor {motor_index+1}", command=lambda idx=motor_index: start_motor(idx), bg='green', fg='white', font=("Arial", 14, "bold"))
    start_button.grid(row=0, column=0, padx=1, pady=2)

    stop_button = tk.Button(motor_frame, text=f"Stop \nMotor {motor_index+1}", command=lambda idx=motor_index: stop_motor(idx), bg='red', fg='white', font=("Arial", 14, "bold"))
    stop_button.grid(row=0, column=1, padx=1, pady=2)

    direction_button = tk.Button(motor_frame, text=f"Direction \n{motor_index+1}", command=lambda idx=motor_index: toggle_direction(idx), bg='purple', fg='white', font=("Arial", 14, "bold"))
    direction_button.grid(row=0, column=2, padx=1, pady=2)

    speed_slider = tk.Scale(motor_frame, from_=1, to=255, orient=tk.HORIZONTAL, font=("Arial", 12), length=200, sliderlength=50, command=lambda value, idx=motor_index: update_speed(idx, value))
    speed_slider.set(motor_speed[motor_index])
    speed_slider.grid(row=0, column=3, padx=5, pady=8)
    speed_sliders.append(speed_slider)

def update_ramp_time(value):
    global ramp_up_time
    ramp_up_time = float(value)

def increase_on_duration():
    global motor_on_duration
    if motor_on_duration < 3:
        motor_on_duration += 0.1
    on_duration_label.config(text="{:.1f}".format(motor_on_duration))

def decrease_on_duration():
    global motor_on_duration
    if motor_on_duration > 0.1:  # Ensure it doesn't go below 0.1
        motor_on_duration -= 0.1
    on_duration_label.config(text="{:.1f}".format(motor_on_duration))

def increase_off_duration():
    global motor_off_duration
    if motor_off_duration < 3:
        motor_off_duration += 0.1
    off_duration_label.config(text="{:.1f}".format(motor_off_duration))

def decrease_off_duration():
    global motor_off_duration
    if motor_off_duration > 0.1:  # Ensure it doesn't go below 0.1
        motor_off_duration -= 0.1
    off_duration_label.config(text="{:.1f}".format(motor_off_duration))

root = tk.Tk()
root.title("PULSE Stepper Motor Control")
root.geometry("800x450")
root.configure(bg='black')

canvas = tk.Canvas(root, bg='black')
canvas.pack(side="left", fill="both", expand=True)

frame = tk.Frame(canvas, bg='black')
canvas.create_window((0, 0), window=frame, anchor="nw")

welcome_label = tk.Label(frame, text="Welcome to PULSE PiClyde!", bg='black', fg='red', font=("Arial", 18, "bold"))
welcome_label.grid(row=1, column=1, columnspan=3, pady=5)

for i in range(6):
    create_motor_control(frame, i, i+1)

stop_all_motors_button = tk.Button(frame, text="Stop All Motors", command=stop_all_motors, bg='blue', fg='white', font=("Arial", 20, "bold"))
stop_all_motors_button.grid(row=2, column=1, columnspan=2, padx=0, pady=0)

quit_program_button = tk.Button(frame, text="Quit Program", command=quit_program, bg='orangered', fg='white', font=("Arial", 18, "bold"))
quit_program_button.grid(row=3, column=1, columnspan=2, padx=0, pady=1)

on_label = tk.Label(frame, text="On", bg='black', fg='white', font=("Arial", 18, "bold"))
on_label.grid(row=4, column=1)

on_duration_label = tk.Label(frame, text="{:.1f}".format(motor_on_duration), bg='black', fg='white', font=("Arial", 18, "bold"))
on_duration_label.grid(row=5, column=1, padx=0, pady=0)

increase_on_button = tk.Button(frame, text="Up", command=increase_on_duration, bg='green', fg='white', font=("Arial", 20, "bold"))
increase_on_button.grid(row=6, column=1, padx=0, pady=0)

decrease_on_button = tk.Button(frame, text="Down", command=decrease_on_duration, bg='red', fg='white', font=("Arial", 18, "bold"))
decrease_on_button.grid(row=7, column=1, padx=0, pady=1)

off_label = tk.Label(frame, text="Off", bg='black', fg='white', font=("Arial", 18, "bold"))
off_label.grid(row=4, column=2, padx=0, pady=1)

off_duration_label = tk.Label(frame, text="{:.1f}".format(motor_off_duration), bg='black', fg='white', font=("Arial", 18, "bold"))
off_duration_label.grid(row=5, column=2, padx=0, pady=1)

increase_off_button = tk.Button(frame, text="Up", command=increase_off_duration, bg='green', fg='white', font=("Arial", 20, "bold"))
increase_off_button.grid(row=6, column=2, padx=0, pady=0)

decrease_off_button = tk.Button(frame, text="Down", command=decrease_off_duration, bg='red', fg='white', font=("Arial", 18, "bold"))
decrease_off_button.grid(row=7, column=2, padx=0, pady=1)

# Add a Spinbox for ramp-up time adjustment
ramp_time_spinbox = tk.Spinbox(frame, from_=0, to=5, increment=0.1, font=("Arial", 18, "bold"), command=lambda: update_ramp_time(ramp_time_spinbox.get()))
ramp_time_spinbox.delete(0, "end")
ramp_time_spinbox.insert(0, str(ramp_up_time))
ramp_time_spinbox.grid(row=7, column=0, columnspan=1, pady=0)

canvas.update_idletasks()
canvas.config(scrollregion=canvas.bbox("all"))

root.mainloop()
