# hotbox-pico
Lightweight Coffee Roasting reporter module based on the Raspberry Pi Pico microcontroller line

## Python Env

Uses *venv* to create and maintain a virtual environment for python to run in.
To create:

1. Navigate to your project directory in VSCode's terminal
    - (For example: `cd Users/user_name/Documents/projects/hotbox-pico`, but use the path of the cloned github repo)
1. Run `python3 -m venv venv`
    - The second venv is the name of the folder, which we are just going to call venv for ease of use
1. Run `source venv/bin/activate`
    - This starts the envirnoment and must be done every time VSCode is opened.
1. Use the template `pip install *package-name*` to install the following modules:
    - adafruit-ampy
    - mpy-cross
    - esptool

## VSCode Env

1. Install the *MicroPico* extension
1. Use `Ctrl+Shift+P` to search for micropico command `Setup MicroPico Project` and run it.
    - This will add a few files and will show the pico commands in the very bottom left of VScode
1. Plug in Pico

run `scripts/connect_to_wifi.py` on a connected Pico W, then `import mip` and `mip.install('aioble')` to install the *aioble* package directly to the Pico W