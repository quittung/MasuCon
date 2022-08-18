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
    timeout: float = 1
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
            # try to load the settings file
            with open(path, "r", encoding="utf-8") as f:
                settings_json = json.load(f)
                return Settings(**settings_json)

        except FileNotFoundError:
            # generate a new one if not found
            settings = Settings()
            with open(path, "w", encoding="utf-8") as f:
                json.dump(settings.__dict__, f, indent=4)
            return settings

        except TypeError as e:
            # alert user if settings file is incompatible
            print("Error occurred while reading settings:")
            print(e)
            print("Using default settings for now. Try regenerating the settings file and transfer your changes manually.")

            return Settings()


def clean_read(port) -> str:
    """Reads a line from a port, converts it to a string and removes whitespace."""
    response = port.readline()
    response = response.decode("ascii")
    response = response.strip()    
    return response


def find_port(id: str, timeout: float) -> typing.Optional[serial.Serial]:
    """Tries to find the controller by going through all available ports until one responds with the correct ID."""
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
                timeout = timeout
            )   

            # ask for id
            for _ in range(3):
                # ask device to identify itself
                port.write(b"id\r\n")      

                # wait for response
                response = clean_read(port)

                # check if response is correct
                if response:
                    if response == id:
                        # controller found, return port
                        return port
                    else:
                        print("Wrong response")
                else:
                    print("No response")
            
            # close port
            port.close()

        except Exception as e:
            # just ignore all errors and try the next port
            print(f"Error: {e}")
            continue


def press_key(key: str, controller: Controller, delay_before_release: float = 0.1, delay_after_release: float = 0) -> None:
    """Presses a key on the keyboard and releases it after a delay."""
    controller.press(key)
    time.sleep(delay_before_release)
    controller.release(key)
    time.sleep(delay_after_release)


def press_key_debug(key: str) -> None:
    print(key, end="")


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
    """Converts a lever position to a string."""
    if lever_pos == 0: 
        return "N"
    elif lever_pos > 0:
        return f"P{lever_pos}"
    else:
        if lever_pos < settings.lever_max_service_brake:
            return "EB"
        else:
            return f"B{abs(lever_pos)}"


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


    # connect to MasuCon
    print("Connecting to MasuCon...")
    masucon = find_port(settings.controller_id, settings.timeout)

    if not masucon:
        print("Unable to establish connection to MasuCon")
        return

    print("Connection established")


    # main loop
    print("Starting main loop...")
    lever_guess = 0
    while True:
        try:
            lever_physical = int(clean_read(masucon))
        except ValueError:
            # controller sent text or empty line, just ignore it
            continue 

        lever_target = map_lever(lever_physical, settings)
        lever_str = lever_to_str(lever_target, settings)

        # determine whether to go up or down
        direction = 1 if lever_target > lever_guess  else -1

        # list all lever positions from the assumed position to the target position
        # in reverse order, without the current position
        postition_list = list(range(lever_target, lever_guess, -direction))

        # create a list of steps to get to the target
        steps: list[str] = []
        for p in postition_list:
            step_string = lever_to_str(p, settings).lower()

            if step_string in settings.buttons:
                # if one of the positions can be accessed directly, do that and just start there
                steps.append(settings.buttons[step_string])
                break

            else:
                # else just step up or down as neccessary
                if direction == 1:
                    steps.append(settings.buttons["up"])
                else:
                    steps.append(settings.buttons["down"])

        # reverse the list to get in the right order
        steps.reverse()

        # if already on a target that can be directly accessed, repress that button just to be sure
        if len(steps) == 0 and lever_str.lower() in settings.buttons:
            steps.append(settings.buttons[lever_str.lower()])
        
        # send button presses as described in the step list
        for s in steps:
            # press_key_simple(s)
            press_key_debug(s) # DEBUG ONLY, use press_key_simple for actual operation

        # update assumed position
        lever_guess = lever_target

        # verbose output for debugging
        print(lever_physical)
        print(lever_target)
        print(lever_str)
        print(steps)
        print()

        # sleep a bit 
        time.sleep(0.01)
        

if __name__ == "__main__":
    main()