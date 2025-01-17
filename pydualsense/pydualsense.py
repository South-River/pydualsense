import logging
import os
import sys
from sys import platform

if platform.startswith('Windows') and sys.version_info >= (3, 8):
    os.add_dll_directory(os.getcwd())

import hidapi
from .enums import (LedOptions, PlayerID, PulseOptions, TriggerModes, Brightness, ConnectionType) # type: ignore
import threading
from .event_system import Event
from copy import deepcopy

import array

logger = logging.getLogger()
FORMAT = '%(asctime)s %(message)s'
logging.basicConfig(format=FORMAT)
logger.setLevel(logging.INFO)

hashTable = array.array('I', [
    0xd202ef8d, 0xa505df1b, 0x3c0c8ea1, 0x4b0bbe37, 0xd56f2b94, 0xa2681b02, 0x3b614ab8, 0x4c667a2e,
    0xdcd967bf, 0xabde5729, 0x32d70693, 0x45d03605, 0xdbb4a3a6, 0xacb39330, 0x35bac28a, 0x42bdf21c,
    0xcfb5ffe9, 0xb8b2cf7f, 0x21bb9ec5, 0x56bcae53, 0xc8d83bf0, 0xbfdf0b66, 0x26d65adc, 0x51d16a4a,
    0xc16e77db, 0xb669474d, 0x2f6016f7, 0x58672661, 0xc603b3c2, 0xb1048354, 0x280dd2ee, 0x5f0ae278,
    0xe96ccf45, 0x9e6bffd3, 0x762ae69, 0x70659eff, 0xee010b5c, 0x99063bca, 0xf6a70, 0x77085ae6,
    0xe7b74777, 0x90b077e1, 0x9b9265b, 0x7ebe16cd, 0xe0da836e, 0x97ddb3f8, 0xed4e242, 0x79d3d2d4,
    0xf4dbdf21, 0x83dcefb7, 0x1ad5be0d, 0x6dd28e9b, 0xf3b61b38, 0x84b12bae, 0x1db87a14, 0x6abf4a82,
    0xfa005713, 0x8d076785, 0x140e363f, 0x630906a9, 0xfd6d930a, 0x8a6aa39c, 0x1363f226, 0x6464c2b0,
    0xa4deae1d, 0xd3d99e8b, 0x4ad0cf31, 0x3dd7ffa7, 0xa3b36a04, 0xd4b45a92, 0x4dbd0b28, 0x3aba3bbe,
    0xaa05262f, 0xdd0216b9, 0x440b4703, 0x330c7795, 0xad68e236, 0xda6fd2a0, 0x4366831a, 0x3461b38c,
    0xb969be79, 0xce6e8eef, 0x5767df55, 0x2060efc3, 0xbe047a60, 0xc9034af6, 0x500a1b4c, 0x270d2bda,
    0xb7b2364b, 0xc0b506dd, 0x59bc5767, 0x2ebb67f1, 0xb0dff252, 0xc7d8c2c4, 0x5ed1937e, 0x29d6a3e8,
    0x9fb08ed5, 0xe8b7be43, 0x71beeff9, 0x6b9df6f, 0x98dd4acc, 0xefda7a5a, 0x76d32be0, 0x1d41b76,
    0x916b06e7, 0xe66c3671, 0x7f6567cb, 0x862575d, 0x9606c2fe, 0xe101f268, 0x7808a3d2, 0xf0f9344,
    0x82079eb1, 0xf500ae27, 0x6c09ff9d, 0x1b0ecf0b, 0x856a5aa8, 0xf26d6a3e, 0x6b643b84, 0x1c630b12,
    0x8cdc1683, 0xfbdb2615, 0x62d277af, 0x15d54739, 0x8bb1d29a, 0xfcb6e20c, 0x65bfb3b6, 0x12b88320,
    0x3fba6cad, 0x48bd5c3b, 0xd1b40d81, 0xa6b33d17, 0x38d7a8b4, 0x4fd09822, 0xd6d9c998, 0xa1def90e,
    0x3161e49f, 0x4666d409, 0xdf6f85b3, 0xa868b525, 0x360c2086, 0x410b1010, 0xd80241aa, 0xaf05713c,
    0x220d7cc9, 0x550a4c5f, 0xcc031de5, 0xbb042d73, 0x2560b8d0, 0x52678846, 0xcb6ed9fc, 0xbc69e96a,
    0x2cd6f4fb, 0x5bd1c46d, 0xc2d895d7, 0xb5dfa541, 0x2bbb30e2, 0x5cbc0074, 0xc5b551ce, 0xb2b26158,
    0x4d44c65, 0x73d37cf3, 0xeada2d49, 0x9ddd1ddf, 0x3b9887c, 0x74beb8ea, 0xedb7e950, 0x9ab0d9c6,
    0xa0fc457, 0x7d08f4c1, 0xe401a57b, 0x930695ed, 0xd62004e, 0x7a6530d8, 0xe36c6162, 0x946b51f4,
    0x19635c01, 0x6e646c97, 0xf76d3d2d, 0x806a0dbb, 0x1e0e9818, 0x6909a88e, 0xf000f934, 0x8707c9a2,
    0x17b8d433, 0x60bfe4a5, 0xf9b6b51f, 0x8eb18589, 0x10d5102a, 0x67d220bc, 0xfedb7106, 0x89dc4190,
    0x49662d3d, 0x3e611dab, 0xa7684c11, 0xd06f7c87, 0x4e0be924, 0x390cd9b2, 0xa0058808, 0xd702b89e,
    0x47bda50f, 0x30ba9599, 0xa9b3c423, 0xdeb4f4b5, 0x40d06116, 0x37d75180, 0xaede003a, 0xd9d930ac,
    0x54d13d59, 0x23d60dcf, 0xbadf5c75, 0xcdd86ce3, 0x53bcf940, 0x24bbc9d6, 0xbdb2986c, 0xcab5a8fa,
    0x5a0ab56b, 0x2d0d85fd, 0xb404d447, 0xc303e4d1, 0x5d677172, 0x2a6041e4, 0xb369105e, 0xc46e20c8,
    0x72080df5, 0x50f3d63, 0x9c066cd9, 0xeb015c4f, 0x7565c9ec, 0x262f97a, 0x9b6ba8c0, 0xec6c9856,
    0x7cd385c7, 0xbd4b551, 0x92dde4eb, 0xe5dad47d, 0x7bbe41de, 0xcb97148, 0x95b020f2, 0xe2b71064,
    0x6fbf1d91, 0x18b82d07, 0x81b17cbd, 0xf6b64c2b, 0x68d2d988, 0x1fd5e91e, 0x86dcb8a4, 0xf1db8832,
    0x616495a3, 0x1663a535, 0x8f6af48f, 0xf86dc419, 0x660951ba, 0x110e612c, 0x88073096, 0xff000000
])

def compute(buffer, len):
    result = 0xeada2d49
    
    for i in range(0, len):
        result = hashTable[(result&0xFF)^(buffer[i]&0xFF)]^(result>>8)
        
    return result

class pydualsense:

    def __init__(self, verbose: bool = False) -> None:
        """
        initialise the library but dont connect to the controller. call :func:`init() <pydualsense.pydualsense.init>` to connect to the controller

        Args:
            verbose (bool, optional): display verbose out (debug prints of input and output). Defaults to False.
        """
        # TODO: maybe add a init function to not automatically allocate controller when class is declared
        self.verbose = verbose

        if self.verbose:
            logger.setLevel(logging.DEBUG)

        self.leftMotor = 0
        self.rightMotor = 0

        self.last_states = None

        self.register_available_events()

    def register_available_events(self) -> None:
        """
        register all available events that can be used for the controller
        """

        # button events
        self.triangle_pressed = Event()
        self.circle_pressed = Event()
        self.cross_pressed = Event()
        self.square_pressed = Event()

        # dpad events
        # TODO: add a event that sends the pressed key if any key is pressed
        # self.dpad_changed = Event()
        self.dpad_up = Event()
        self.dpad_down = Event()
        self.dpad_left = Event()
        self.dpad_right = Event()

        # joystick
        self.left_joystick_changed = Event()
        self.right_joystick_changed = Event()

        # trigger back buttons
        self.r1_changed = Event()
        self.r2_changed = Event()
        self.r3_changed = Event()

        self.l1_changed = Event()
        self.l2_changed = Event()
        self.l3_changed = Event()

        # misc
        self.ps_pressed = Event()
        self.touch_pressed = Event()
        self.microphone_pressed = Event()
        self.share_pressed = Event()
        self.option_pressed = Event()

        # trackpad touch
        # handles 1 or 2 fingers
        #self.trackpad_frame_reported = Event()

        # gyrometer events
        self.gyro_changed = Event()

        self.accelerometer_changed = Event()

    def init(self) -> None:
        """
        initialize module and device states. Starts the sendReport background thread at the end
        """
        self.device: hidapi.Device = self.__find_device()
        self.light = DSLight() # control led light of ds
        self.audio = DSAudio() # ds audio setting
        self.triggerL = DSTrigger() # left trigger
        self.triggerR = DSTrigger() # right trigger
        self.state = DSState() # controller states
        self.conType = self.determineConnectionType() # determine USB or BT connection
        self.ds_thread = True
        self.report_thread = threading.Thread(target=self.sendReport)
        self.report_thread.start()
        self.states = None

    def determineConnectionType(self) -> ConnectionType:
        """
        Determine the connection type of the controller. eg USB or BT.

        We ask the controller for an input report with a length up to 100 bytes
        and afterwords check the lenght of the received input report.
        The connection type determines the length of the report.

        This way of determining is not pretty but it works..

        Returns:
            ConnectionType: Detected connection type of the controller.
        """

        dummy_report = self.device.read(100)
        input_report_length = len(dummy_report)

        if input_report_length == 64:
            self.input_report_length = 64
            self.output_report_length = 64
            return ConnectionType.USB
        elif input_report_length == 78:
            self.input_report_length = 78
            self.output_report_length = 78
            return ConnectionType.BT

    def close(self) -> None:
        """
        Stops the report thread and closes the HID device
        """
        # TODO: reset trigger effect to default

        self.ds_thread = False
        self.report_thread.join()
        self.device.close()

    def __find_device(self) -> hidapi.Device:
        """
        find HID dualsense device and open it

        Raises:
            Exception: HIDGuardian detected
            Exception: No device detected

        Returns:
            hid.Device: returns opened controller device
        """
        # TODO: detect connection mode, bluetooth has a bigger write buffer
        # TODO: implement multiple controllers working
        if sys.platform.startswith('win32'):
            import pydualsense.hidguardian as hidguardian
            if hidguardian.check_hide():
                raise Exception('HIDGuardian detected. Delete the controller from HIDGuardian and restart PC to connect to controller')
        detected_device: hidapi.Device = None
        devices = hidapi.enumerate(vendor_id=0x054c)
        for device in devices:
            if device.vendor_id == 0x054c and device.product_id == 0x0CE6:
                detected_device = device

        if detected_device is None:
            raise Exception('No device detected')

        dual_sense = hidapi.Device(vendor_id=detected_device.vendor_id, product_id=detected_device.product_id)
        return dual_sense

    def setLeftMotor(self, intensity: int) -> None:
        """
        set left motor rumble

        Args:
            intensity (int): rumble intensity

        Raises:
            TypeError: intensity false type
            Exception: intensity out of bounds 0..255
        """
        if not isinstance(intensity, int):
            raise TypeError('left motor intensity needs to be an int')

        if intensity > 255 or intensity < 0:
            raise Exception('maximum intensity is 255')
        self.leftMotor = intensity

    def setRightMotor(self, intensity: int) -> None:
        """
        set right motor rumble

        Args:
            intensity (int): rumble intensity

        Raises:
            TypeError: intensity false type
            Exception: intensity out of bounds 0..255
        """
        if not isinstance(intensity, int):
            raise TypeError('right motor intensity needs to be an int')

        if intensity > 255 or intensity < 0:
            raise Exception('maximum intensity is 255')
        self.rightMotor = intensity

    def sendReport(self) -> None:
        """background thread handling the reading of the device and updating its states
        """
        while self.ds_thread:
            # read data from the input report of the controller
            inReport = self.device.read(self.input_report_length)
            if self.verbose:
                logger.debug(inReport)
            # decrypt the packet and bind the inputs
            self.readInput(inReport)

            # prepare new report for device
            outReport = self.prepareReport()

            # write the report to the device
            self.writeReport(outReport)

    def readInput(self, inReport) -> None:
        """
        read the input from the controller and assign the states

        Args:
            inReport (bytearray): read bytearray containing the state of the whole controller
        """
        if self.conType == ConnectionType.BT:
            # the reports for BT and USB are structured the same,
            # but there is one more byte at the start of the bluetooth report.
            # We drop that byte, so that the format matches up again.
            states = list(inReport)[1:] # convert bytes to list
        else: # USB
            states = list(inReport) # convert bytes to list

        self.states = states
        # states 0 is always 1
        self.state.LX = states[1] - 127
        self.state.LY = states[2] - 127
        self.state.RX = states[3] - 127
        self.state.RY = states[4] - 127
        self.state.L2 = states[5]
        self.state.R2 = states[6]

        # state 7 always increments -> not used anywhere

        buttonState = states[8]
        self.state.triangle = (buttonState & (1 << 7)) != 0
        self.state.circle = (buttonState & (1 << 6)) != 0
        self.state.cross = (buttonState & (1 << 5)) != 0
        self.state.square = (buttonState & (1 << 4)) != 0

        # dpad
        dpad_state = buttonState & 0x0F
        self.state.setDPadState(dpad_state)

        misc = states[9]
        self.state.R3 = (misc & (1 << 7)) != 0
        self.state.L3 = (misc & (1 << 6)) != 0
        self.state.options = (misc & (1 << 5)) != 0
        self.state.share = (misc & (1 << 4)) != 0
        self.state.R2Btn = (misc & (1 << 3)) != 0
        self.state.L2Btn = (misc & (1 << 2)) != 0
        self.state.R1 = (misc & (1 << 1)) != 0
        self.state.L1 = (misc & (1 << 0)) != 0

        misc2 = states[10]
        self.state.ps = (misc2 & (1 << 0)) != 0
        self.state.touchBtn = (misc2 & 0x02) != 0
        self.state.micBtn = (misc2 & 0x04) != 0

        # trackpad touch
        self.state.trackPadTouch0.ID = states[33] & 0x7F
        self.state.trackPadTouch0.isActive = (states[33] & 0x80) == 0
        self.state.trackPadTouch0.X = ((states[35] & 0x0f) << 8) | (states[34])
        self.state.trackPadTouch0.Y = ((states[36]) << 4) | ((states[35] & 0xf0) >> 4)

        # trackpad touch
        self.state.trackPadTouch1.ID = states[37] & 0x7F
        self.state.trackPadTouch1.isActive = (states[37] & 0x80) == 0
        self.state.trackPadTouch1.X = ((states[39] & 0x0f) << 8) | (states[38])
        self.state.trackPadTouch1.Y = ((states[40]) << 4) | ((states[39] & 0xf0) >> 4)

        # gyro
        self.state.gyro.Pitch = int.from_bytes(([states[16], states[17]]), byteorder='little', signed=True)
        self.state.gyro.Yaw = int.from_bytes(([states[18], states[19]]), byteorder='little', signed=True)
        self.state.gyro.Roll = int.from_bytes(([states[20], states[21]]), byteorder='little', signed=True)

        # accelerometer
        self.state.accelerometer.X = int.from_bytes(([states[22], states[23]]), byteorder='little', signed=True)
        self.state.accelerometer.Y = int.from_bytes(([states[24], states[25]]), byteorder='little', signed=True)
        self.state.accelerometer.Z = int.from_bytes(([states[26], states[27]]), byteorder='little', signed=True)

        # first call we dont have a "last state" so we create if with the first occurence
        if self.last_states is None:
            self.last_states = deepcopy(self.state)
            return

        # send all events if neede
        if self.state.circle != self.last_states.circle:
            self.circle_pressed(self.state.circle)

        if self.state.cross != self.last_states.cross:
            self.cross_pressed(self.state.cross)

        if self.state.triangle != self.last_states.triangle:
            self.triangle_pressed(self.state.triangle)

        if self.state.square != self.last_states.square:
            self.square_pressed(self.state.square)

        if self.state.DpadDown != self.last_states.DpadDown:
            self.dpad_down(self.state.DpadDown)

        if self.state.DpadLeft != self.last_states.DpadLeft:
            self.dpad_left(self.state.DpadLeft)

        if self.state.DpadRight != self.last_states.DpadRight:
            self.dpad_right(self.state.DpadRight)

        if self.state.DpadUp != self.last_states.DpadUp:
            self.dpad_up(self.state.DpadUp)

        if self.state.LX != self.last_states.LX or self.state.LY != self.last_states.LY:
            self.left_joystick_changed(self.state.LX, self.state.LY)

        if self.state.RX != self.last_states.RX or self.state.RY != self.last_states.RY:
            self.right_joystick_changed(self.state.RX, self.state.RY)

        if self.state.R1 != self.last_states.R1:
            self.r1_changed(self.state.R1)

        if self.state.R2 != self.last_states.R2:
            self.r2_changed(self.state.R2)

        if self.state.L1 != self.last_states.L1:
            self.l1_changed(self.state.L1)

        if self.state.L2 != self.last_states.L2:
            self.l2_changed(self.state.L2)

        if self.state.R3 != self.last_states.R3:
            self.r3_changed(self.state.R3)

        if self.state.L3 != self.last_states.L3:
            self.l3_changed(self.state.L3)

        if self.state.ps != self.last_states.ps:
            self.ps_pressed(self.state.ps)

        if self.state.touchBtn != self.last_states.touchBtn:
            self.touch_pressed(self.state.touchBtn)

        if self.state.micBtn != self.last_states.micBtn:
            self.microphone_pressed(self.state.micBtn)

        if self.state.share != self.last_states.share:
            self.share_pressed(self.state.share)

        if self.state.options != self.last_states.options:
            self.option_pressed(self.state.options)

        if self.state.accelerometer.X != self.last_states.accelerometer.X or \
            self.state.accelerometer.Y != self.last_states.accelerometer.Y or \
                self.state.accelerometer.Z != self.last_states.accelerometer.Z:
            self.accelerometer_changed(self.state.accelerometer.X, self.state.accelerometer.Y, self.state.accelerometer.Z)

        if self.state.gyro.Pitch != self.last_states.gyro.Pitch or \
            self.state.gyro.Yaw != self.last_states.gyro.Yaw or \
                self.state.gyro.Roll != self.last_states.gyro.Roll:
            self.gyro_changed(self.state.gyro.Pitch, self.state.gyro.Yaw, self.state.gyro.Roll)

        """
        copy current state into temp object to check next cycle if a change occuret
        and event trigger is needed
        """
        self.last_states = deepcopy(self.state) # copy current state into object to check next time

        # TODO: control mouse with touchpad for fun as DS4Windows

    def writeReport(self, outReport) -> None:
        """
        write the report to the device

        Args:
            outReport (list): report to be written to device
        """
        self.device.write(bytes(outReport))

    def prepareReport(self) -> None:
        """
        prepare the output to be send to the controller

        Returns:
            list: report to send to controller
        """
        if self.conType == ConnectionType.USB:
            outReport = [0] * self.output_report_length # create empty list with range of output report
            # packet type
            outReport[0] = 0x2

            # flags determing what changes this packet will perform
            # 0x01 set the main motors (also requires flag 0x02); setting this by itself will allow rumble to gracefully terminate and then re-enable audio haptics, whereas not setting it will kill the rumble instantly and re-enable audio haptics.
            # 0x02 set the main motors (also requires flag 0x01; without bit 0x01 motors are allowed to time out without re-enabling audio haptics)
            # 0x04 set the right trigger motor
            # 0x08 set the left trigger motor
            # 0x10 modification of audio volume
            # 0x20 toggling of internal speaker while headset is connected
            # 0x40 modification of microphone volume
            outReport[1] = 0xff # [1]

            # further flags determining what changes this packet will perform
            # 0x01 toggling microphone LED
            # 0x02 toggling audio/mic mute
            # 0x04 toggling LED strips on the sides of the touchpad
            # 0x08 will actively turn all LEDs off? Convenience flag? (if so, third parties might not support it properly)
            # 0x10 toggling white player indicator LEDs below touchpad
            # 0x20 ???
            # 0x40 adjustment of overall motor/effect power (index 37 - read note on triggers)
            # 0x80 ???
            outReport[2] = 0x1 | 0x2 | 0x4 | 0x10 | 0x40 # [2]

            outReport[3] = self.rightMotor # right low freq motor 0-255 # [3]
            outReport[4] = self.leftMotor # left low freq motor 0-255 # [4]

            # outReport[5] - outReport[8] audio related

            # set Micrphone LED, setting doesnt effect microphone settings
            outReport[9] = self.audio.microphone_led # [9]

            outReport[10] = 0x10 if self.audio.microphone_mute is True else 0x00

            # add right trigger mode + parameters to packet
            outReport[11] = self.triggerR.mode.value
            outReport[12] = self.triggerR.forces[0]
            outReport[13] = self.triggerR.forces[1]
            outReport[14] = self.triggerR.forces[2]
            outReport[15] = self.triggerR.forces[3]
            outReport[16] = self.triggerR.forces[4]
            outReport[17] = self.triggerR.forces[5]
            outReport[20] = self.triggerR.forces[6]

            outReport[22] = self.triggerL.mode.value
            outReport[23] = self.triggerL.forces[0]
            outReport[24] = self.triggerL.forces[1]
            outReport[25] = self.triggerL.forces[2]
            outReport[26] = self.triggerL.forces[3]
            outReport[27] = self.triggerL.forces[4]
            outReport[28] = self.triggerL.forces[5]
            outReport[31] = self.triggerL.forces[6]

            outReport[39] = self.light.ledOption.value
            outReport[42] = self.light.pulseOptions.value
            outReport[43] = self.light.brightness.value
            outReport[44] = self.light.playerNumber.value
            outReport[45] = self.light.TouchpadColor[0]
            outReport[46] = self.light.TouchpadColor[1]
            outReport[47] = self.light.TouchpadColor[2]
        
        elif self.conType == ConnectionType.BT:
            outReport = [0]*self.output_report_length

            outReport[0] = 0x31
            outReport[1] = 0x02

            outReport[2] = 0xff

            outReport[3] = 0x1 | 0x2 | 0x4 | 0x10 | 0x40 # [2]

            outReport[4] = self.rightMotor # right low freq motor 0-255 # [4]
            outReport[5] = self.leftMotor # left low freq motor 0-255 # [5]

            outReport[10] = self.audio.microphone_led # [10]

            outReport[11] = 0x10 if self.audio.microphone_mute is True else 0x00

            # add right trigger mode + parameters to packet
            outReport[12] = self.triggerR.mode.value
            outReport[13] = self.triggerR.forces[0]
            outReport[14] = self.triggerR.forces[1]
            outReport[15] = self.triggerR.forces[2]
            outReport[16] = self.triggerR.forces[3]
            outReport[17] = self.triggerR.forces[4]
            outReport[18] = self.triggerR.forces[5]
            outReport[21] = self.triggerR.forces[6]

            outReport[23] = self.triggerL.mode.value
            outReport[24] = self.triggerL.forces[0]
            outReport[25] = self.triggerL.forces[1]
            outReport[26] = self.triggerL.forces[2]
            outReport[27] = self.triggerL.forces[3]
            outReport[28] = self.triggerL.forces[4]
            outReport[29] = self.triggerL.forces[5]
            outReport[32] = self.triggerL.forces[6]

            outReport[40] = self.light.ledOption.value
            outReport[43] = self.light.pulseOptions.value
            outReport[44] = self.light.brightness.value
            outReport[45] = self.light.playerNumber.value
            outReport[46] = self.light.TouchpadColor[0]
            outReport[47] = self.light.TouchpadColor[1]
            outReport[48] = self.light.TouchpadColor[2]

            crcChecksum = compute(outReport, 74)

            outReport[74] = (crcChecksum & 0x000000FF)
            outReport[75] = (crcChecksum & 0x0000FF00) >> 8
            outReport[76] = (crcChecksum & 0x00FF0000) >> 16
            outReport[77] = (crcChecksum & 0xFF000000) >> 24

        if self.verbose:
            logger.debug(outReport)

        return outReport


class DSTouchpad:
    """
    Dualsense Touchpad class. Contains X and Y position of touch and if the touch isActive
    """
    def __init__(self) -> None:
        """
        Class represents the Touchpad of the controller
        """
        self.isActive = False
        self.ID = 0
        self.X = 0
        self.Y = 0


class DSState:

    def __init__(self) -> None:
        """
        All dualsense states (inputs) that can be read. Second method to check if a input is pressed.
        """
        self.square, self.triangle, self.circle, self.cross = False, False, False, False
        self.DpadUp, self.DpadDown, self.DpadLeft, self.DpadRight = False, False, False, False
        self.L1, self.L2, self.L3, self.R1, self.R2, self.R3, self.R2Btn, self.L2Btn = False, False, False, False, False, False, False, False
        self.share, self.options, self.ps, self.touch1, self.touch2, self.touchBtn, self.touchRight, self.touchLeft = False, False, False, False, False, False, False, False
        self.touchFinger1, self.touchFinger2 = False, False
        self.micBtn = False
        self.RX, self.RY, self.LX, self.LY = 128, 128, 128, 128
        self.trackPadTouch0, self.trackPadTouch1 = DSTouchpad(), DSTouchpad()
        self.gyro = DSGyro()
        self.accelerometer = DSAccelerometer()

    def setDPadState(self, dpad_state: int):
        """
        Sets the dpad state variables according to the integers that was read from the controller

        Args:
            dpad_state (int): integer number representing the dpad state
        """
        if dpad_state == 0:
            self.DpadUp = True
            self.DpadDown = False
            self.DpadLeft = False
            self.DpadRight = False
        elif dpad_state == 1:
            self.DpadUp = True
            self.DpadDown = False
            self.DpadLeft = False
            self.DpadRight = True
        elif dpad_state == 2:
            self.DpadUp = False
            self.DpadDown = False
            self.DpadLeft = False
            self.DpadRight = True
        elif dpad_state == 3:
            self.DpadUp = False
            self.DpadDown = True
            self.DpadLeft = False
            self.DpadRight = True
        elif dpad_state == 4:
            self.DpadUp = False
            self.DpadDown = True
            self.DpadLeft = False
            self.DpadRight = False
        elif dpad_state == 5:
            self.DpadUp = False
            self.DpadDown = True
            self.DpadLeft = False
            self.DpadRight = False
        elif dpad_state == 6:
            self.DpadUp = False
            self.DpadDown = False
            self.DpadLeft = True
            self.DpadRight = False
        elif dpad_state == 7:
            self.DpadUp = True
            self.DpadDown = False
            self.DpadLeft = True
            self.DpadRight = False
        else:
            self.DpadUp = False
            self.DpadDown = False
            self.DpadLeft = False
            self.DpadRight = False


class DSLight:
    """
    Represents all features of lights on the controller
    """
    def __init__(self) -> None:
        self.brightness: Brightness = Brightness.low # sets
        self.playerNumber: PlayerID = PlayerID.PLAYER_1
        self.ledOption: LedOptions = LedOptions.Both
        self.pulseOptions: PulseOptions = PulseOptions.Off
        self.TouchpadColor = (0, 0, 255)

    def setLEDOption(self, option: LedOptions):
        """
        Sets the LED Option

        Args:
            option (LedOptions): Led option

        Raises:
            TypeError: LedOption is false type
        """
        if not isinstance(option, LedOptions):
            raise TypeError('Need LEDOption type')
        self.ledOption = option

    def setPulseOption(self, option: PulseOptions):
        """
        Sets the Pulse Option of the LEDs

        Args:
            option (PulseOptions): pulse option of the LEDs

        Raises:
            TypeError: Pulse option is false type
        """
        if not isinstance(option, PulseOptions):
            raise TypeError('Need PulseOption type')
        self.pulseOptions = option

    def setBrightness(self, brightness: Brightness):
        """
        Defines the brightness of the Player LEDs

        Args:
            brightness (Brightness): brightness of LEDS

        Raises:
            TypeError: brightness false type
        """
        if not isinstance(brightness, Brightness):
            raise TypeError('Need Brightness type')
        self.brightness = brightness

    def setPlayerID(self, player: PlayerID):
        """
        Sets the PlayerID of the controller with the choosen LEDs.
        The controller has 4 Player states

        Args:
            player (PlayerID): chosen PlayerID for the Controller

        Raises:
            TypeError: [description]
        """
        if not isinstance(player, PlayerID):
            raise TypeError('Need PlayerID type')
        self.playerNumber = player

    def setColorI(self, r: int, g: int, b: int) -> None:
        """
        Sets the Color around the Touchpad of the controller

        Args:
            r (int): red channel
            g (int): green channel
            b (int): blue channel

        Raises:
            TypeError: color channels have wrong type
            Exception: color channels are out of bounds
        """
        if not isinstance(r, int) or not isinstance(g, int) or not isinstance(b, int):
            raise TypeError('Color parameter need to be int')
        # check if color is out of bounds
        if (r > 255 or g > 255 or b > 255) or (r < 0 or g < 0 or b < 0):
            raise Exception('colors have values from 0 to 255 only')
        self.TouchpadColor = (r, g, b)

    def setColorT(self, color: tuple) -> None:
        """
        Sets the Color around the Touchpad as a tuple

        Args:
            color (tuple): color as tuple

        Raises:
            TypeError: color has wrong type
            Exception: color channels are out of bounds
        """
        if not isinstance(color, tuple):
            raise TypeError('Color type is tuple')
        # unpack for out of bounds check
        r, g, b = map(int, color)
        # check if color is out of bounds
        if (r > 255 or g > 255 or b > 255) or (r < 0 or g < 0 or b < 0):
            raise Exception('colors have values from 0 to 255 only')
        self.TouchpadColor = (r, g, b)


class DSAudio:
    def __init__(self) -> None:
        """
        initialize the limited Audio features of the controller
        """
        self.microphone_mute = 0
        self.microphone_led = 0

    def setMicrophoneLED(self, value):
        """
        Activates or disables the microphone led.
        This doesnt change the mute/unmutes the microphone itself.

        Args:
            value (bool): On or off microphone LED

        Raises:
            Exception: false state for the led
        """
        if not isinstance(value, bool):
            raise TypeError('MicrophoneLED can only be a bool')
        self.microphone_led = value

    def setMicrophoneState(self, state: bool):
        """
        Set the microphone state and also sets the microphone led accordingle

        Args:
            state (bool): desired state of the microphone

        Raises:
            TypeError: state was not a bool
        """

        if not isinstance(state, bool):
            raise TypeError('state needs to be bool')

        self.setMicrophoneLED(state) # set led accordingly
        self.microphone_mute = state


class DSTrigger:
    """
    Dualsense trigger class. Allowes for multiple :class:`TriggerModes <pydualsense.enums.TriggerModes>` and multiple forces

    # TODO: make this interface more userfriendly so a developer knows what he is doing
    """
    def __init__(self) -> None:
        # trigger modes
        self.mode: TriggerModes = TriggerModes.Off

        # force parameters for the triggers
        self.forces = [0 for i in range(7)]

    def setForce(self, forceID: int = 0, force: int = 0):
        """
        Sets the forces of the choosen force parameter

        Args:
            forceID (int, optional): force parameter. Defaults to 0.
            force (int, optional): applied force to the parameter. Defaults to 0.

        Raises:
            TypeError: wrong type of forceID or force
            Exception: choosen a false force parameter
        """
        if not isinstance(forceID, int) or not isinstance(force, int):
            raise TypeError('forceID and force needs to be type int')

        if forceID > 6 or forceID < 0:
            raise Exception('only 7 parameters available')

        self.forces[forceID] = force

    def setMode(self, mode: TriggerModes):
        """
        Set the Mode for the Trigger

        Args:
            mode (TriggerModes): Trigger mode

        Raises:
            TypeError: false Trigger mode type
        """
        if not isinstance(mode, TriggerModes):
            raise TypeError('Trigger mode parameter needs to be of type `TriggerModes`')

        self.mode = mode


class DSGyro:
    """
    Class representing the Gyro2 of the controller
    """
    def __init__(self) -> None:
        self.Pitch = 0
        self.Yaw = 0
        self.Roll = 0


class DSAccelerometer:
    """
    Class representing the Accelerometer of the controller
    """
    def __init__(self) -> None:
        self.X = 0
        self.Y = 0
        self.Z = 0
