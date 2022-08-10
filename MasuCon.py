from functools import partial
import json
import time
import typing

# required modules: pyserial, pyinput
import serial
import serial.tools.list_ports
from pynput.keyboard import Controller

def find_port(id: str) -> typing.Optional[serial.Serial]:
    port_list = serial.tools.list_ports.comports()
    if not port_list:
        print("No ports found")
        return None

    for port_info in port_list:
        print(f"Testing port: {port_info}")
        try:
            # open port
            port = serial.Serial(
                port = port_info.name, 
                baudrate = 9600,
                timeout = 0.5
            )   

            # ask for id
            port.write(b"id\r\n")      
            response = port.readline()

            if response == id:
                # controller found, return port
                return port
            elif not response:
                print("No response")
            else:
                print("Handshake failed")
            
            # close port
            port.close()

        except Exception as e:
            # just ignore all errors and try the next port
            print(f"Error: {e}")
            continue

def press_key(key: str, controller: Controller, delay_before_release: float = 0.1, delay_after_release: float = 0):
    controller.press(key)
    time.sleep(delay_before_release)
    controller.release(key)
    time.sleep(delay_after_release)

def main():
    print("MasuCon Driver v2.0")

    # load settings
    print("Loading settings...")
    with open("settings.json", "r") as f:
        settings = json.load(f)


    # prepare keyboard controller
    print("Preparing keyboard controller...")
    keyboard_controller = Controller()
    press_key_simple = partial(
        press_key, 
        controller=keyboard_controller, 
        delay_before_release=settings["button_delay_before_release"], 
        delay_after_release=settings["button_delay_after_release"]
    )

    # use like this:
    # press_key_simple("l")


    # connect to MasuCon
    print("Connecting to MasuCon...")
    masucon = find_port(settings["controller_id"])

    if not masucon:
        print("Unable to establish connection to MasuCon")
        return

    print("Connection established")


    # main loop
    print("Starting main loop...")
    while True:
        # TODO: process incoming data and press corresponding keys
        print(masucon.readline())

        time.sleep(0.1)

        # read and process MasuCon state
        # compare to simulator state
        # determine steps to bring sim into sync with MasuCon
        # send corresponding keypresses to simulator
        

if __name__ == "__main__":
    main()