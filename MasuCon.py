from dataclasses import dataclass, field
from functools import partial
import json
from re import L
import time
import typing

# required modules: pyserial, pyinput
import serial
import serial.tools.list_ports
from pynput.keyboard import Controller


@dataclass
class Settings:
    controller_id: str = "masucon"
    lever_max_power: int = 5
    lever_max_service_brake: int = -5
    lever_thresh_emergency_brake: int = -11
    
    buttons: dict[str, str] = field(default_factory=lambda: {
        "up": " ",
        "down": " ",
        "n": " ",
        "b1": " ",
        "eb": " "
    })

    button_delay_before_release: float = 0.1
    button_delay_after_release: float = 0


    @staticmethod
    def from_file(path: str = "settings.json"):
        """Loads settings from file. Generates blank file if not found."""
        try: 
            with open(path, "r", encoding="utf-8") as f:
                settings_json = json.load(f)
                return Settings(**settings_json)
        except FileNotFoundError:
            settings = Settings()
            with open(path, "w", encoding="utf-8") as f:
                json.dump(settings.__dict__, f, indent=4)
            return settings


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


def map_lever(lever_pos: int, settings: Settings) -> int:
    """Maps the physical lever position to what is supported by the sim."""
    if lever_pos > settings.lever_max_power:
        # limit to max power position
        return settings.lever_max_power
        
    elif lever_pos < settings.lever_max_service_brake:
        if lever_pos > settings.lever_thresh_emergency_brake: 
            # limit to max service brake position
            return settings.lever_max_service_brake
        else:
            # set to emergency bake
            return settings.lever_max_service_brake - 1
        
    else:
        # no adjustments necessary
        return lever_pos
    


def lever_to_str(lever_pos: int, settings: Settings) -> str:
    if lever_pos == 0: 
        return "N"
    elif lever_pos > 0:
        return f"P{lever_pos}"
    else:
        if lever_pos < settings.lever_max_service_brake:
            return f"B{lever_pos}"
        else:
            return "EB"


def main():
    print("MasuCon Driver v2.0")

    # load settings
    print("Loading settings...")
    settings = Settings.from_file("settings.json")


    # prepare keyboard controller
    print("Preparing keyboard controller...")
    keyboard_controller = Controller()
    press_key_simple = partial(
        press_key, 
        controller=keyboard_controller, 
        delay_before_release=settings.button_delay_before_release, 
        delay_after_release=settings.button_delay_after_release
    )

    # use like this:
    # press_key_simple("l")


    # connect to MasuCon
    print("Connecting to MasuCon...")
    masucon = find_port(settings.controller_id)

    if not masucon:
        print("Unable to establish connection to MasuCon")
        # return

    print("Connection established")


    # main loop
    print("Starting main loop...")
    while True:
        # TODO: process incoming data and press corresponding keys
        # lever_physical = masucon.readline()
        lever_physical = 7 # DEBUG
        print(lever_physical)
        
        lever_sim = map_lever(lever_physical, settings)
        print(lever_sim)

        lever_str = lever_to_str(lever_sim, settings)
        print(lever_str)

        time.sleep(0.1)

        # read and process MasuCon state
        # compare to simulator state
        # determine steps to bring sim into sync with MasuCon
        # send corresponding keypresses to simulator
        

if __name__ == "__main__":
    main()