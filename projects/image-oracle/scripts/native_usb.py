import termios

import serial


class NativeUsbSerial(serial.Serial):
    # Native USB interprets modem-control transitions as reset/download requests.
    def _update_dtr_state(self):
        pass

    def _update_rts_state(self):
        pass

    def open(self):
        super().open()
        try:
            settings = termios.tcgetattr(self.fileno())
            settings[2] &= ~termios.HUPCL
            termios.tcsetattr(self.fileno(), termios.TCSANOW, settings)
        except Exception:
            self.close()
            raise
