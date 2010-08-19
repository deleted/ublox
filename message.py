#!/usr/bin/env python
import struct
import serial
from datetime import datetime

serial_device = '/dev/cu.usbserial-A900adpX'

msgtypes = {
    'GLL': b'\xf0\x01',
    'RMC': b'\xf0\x04',
    'GSV': b'\xf0\x03',
}

commands = {
    '':'',
    'CFG-MSG': b'\x06\x01',
    'CFG-NAV5': b'\x06\x24',
    'CFG-CFG': b'\x06\x09'
}

class UBXMessage(object):
    """ Base class for UBX messages """
    def __init__(self, command, payload):
       self.sync = b'\xb5\x62' # sync bytes
       self.msgid = commands[command]
       self.payload = payload

    def emit(self):
        #return self.sync + self.msg + bytes(self.checksum)
        msg = struct.pack('cc', self.sync[0], self.sync[1])
        msg += struct.pack('cc', self.msgid[0], self.msgid[1])
        msg += struct.pack('<h', len(self.payload))
        msg += self.payload
        msg += self._checksum(msg[2:]) # slice out the sync bytes
        return msg

    def _checksum(self, msg):
        ck_a = 0x00
        ck_b = 0x00
        b = buffer(msg)
        for i in b:
            ck_a += ord(i)
            ck_a &= 255
            ck_b += ck_a
            ck_b &= 255
        return struct.pack('BB', ck_a, ck_b)

class UBXPollNav5(UBXMessage):
    def __init__(self):
        UBXMessage.__init__(self, 'CFG-NAV5', b'')

class ConfigMessage(UBXMessage):
    def __init__(self, msgtype):
        payload = msgtypes[msgtype]
        command = 'CFG-MSG'
        UBXMessage.__init__(self, command, payload)
        
class UBXSaveConfig(UBXMessage):
    def __init__(self):
        UBXMessage.__init__(self, 'CFG-CFG', b'')
        clearmask = '\x00\x00\x00\x00'
        savemask = '\x0A\x00\x00\x00' # saves msg and nav conf.
        loadmask = '\x00\x00\x00\x00'
        self.payload = clearmask + savemask + loadmask


class NMEA_Message(object):
    """ Base class for NMEA Messages """
    def __init__(self, msgtype, rate):
        self.fields = []

    def emit(self):
        msg = ','.join(self.fields) + self._checksum() + "\r\n"
        return msg
    def _str__(self):
        return self.emit()

    def _checksum(self):
        msg = ','.join(self.fields)[1:]
        checksum = 0
        for char in bytes(msg):
            checksum ^= ord(char)
        #print "Checksum of %s is %s" % (msg, hex(checksum))
        return "*" + hex(checksum)[-2:].upper()

class NMEA_SetRateMsg(NMEA_Message):
    def __init__(self, msgtype, rate):
        self.fields = []
        self.fields.append('$PUBX')
        self.fields.append('40')
        self.fields.append(msgtype)
        for i in range(5):
            self.fields.append(str(rate))
        self.fields.append(str(0))

class NMEA_SetBaudMessage(NMEA_Message):
    def __init__(self, port, baudrate):
        # $PUBX,41,1,0007,0003,19200,0*25
        self.fields = [
            '$PUBX', # message ID
            '41', # MSG ID
            port, #UART Port Num
            # ...etc
        ]

def read_UBX(device):
    timeout_millis = 1000
    byteval = ''
    t0 = datetime.now()
    while byteval != '\xb5':
        dt = datetime.now() - t0
        if dt.seconds * 1000 + dt.microseconds / 1000 > timeout_millis:
            return None
        byteval = device.read()
    msg = byteval
    msg += device.read()
    assert msg[-1] == '\x62' # second sync byte
    msg_id = device.read(2) # msg class and ID
    msg += msg_id
    payload_length_bytes = device.read(2)
    msg += payload_length_bytes
    payload_length = struct.unpack('<h', payload_length_bytes)[0]
    payload = ''
    for i in range(payload_length):
        payload += device.read()
    msg += payload
    msg += device.read(2) # checksum bytes
    m = UBXMessage('','')
    m.msgid = msg_id
    m.payload = payload
    return m


def send(msg):
    #p = open(serial_device, 'wb')
    s = serial.Serial(serial_device)
    s.write(msg.emit())
    output = (read_UBX(s),read_UBX(s))
    s.close()
    return output
    
def save(msg, filename):
    f = open(filename, 'wb')
    f.write(msg.emit())
    f.close()


if __name__ == '__main__':
    m = NMEA_SetRateMsg('GLL',0)
    print m.emit()
