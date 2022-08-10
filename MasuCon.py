import json
import time

# required modules: pyserial, pyinput
import serial
import serial.tools.list_ports
from pynput.keyboard import Controller

def find_port(id: str) -> serial.Serial:
    for port_info in serial.tools.list_ports.comports():
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
            else:
                # wrap up and try next port
                port.close()
        except:
            # just ignore all errors and try the next port
            pass


def main():
    print("MasuCon Driver v2.0")

    # load settings
    print("Loading settings...")
    with open("settings.json", "r") as f:
        settings = json.load(f)

    # connect to MasuCon
    print("Connecting to MasuCon...")
    masucon = find_port(settings["controller_id"])

    if not masucon:
        print("Unable to establish connection to MasuCon")
        return

    print(f"Connection established")


    # main loop
    print("Starting main loop...")
    while True:
        # TODO: process incoming data and press corresponding keys
        print(masucon.readline())

        time.sleep(0.1)




    # keyboard = Controller()
    # keyboard.press('a')
    # keyboard.release('a')

if __name__ == "__main__":
    main()