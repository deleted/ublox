#!/usr/bin/env python
import struct
import serial
from datetime import datetime
import time

#serial_device = '/dev/cu.usbserial-A900adpX'
serial_device = '/dev/cu.usbserial-FTALEZL0'

debug = 0

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
     
    def __str__(self):
        return self.emit()

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
        savemask = '\x0B\x00\x00\x00' # saves ioPort, msg and nav conf.
        loadmask = '\x00\x00\x00\x00'
        self.payload = clearmask + savemask + loadmask


class NMEA_Message(object):
    """ Base class for NMEA Messages """
    def __init__(self, msgtype, rate):
        self.fields = []

    def emit(self):
        msg = ','.join(str(f) for f in self.fields) + self._checksum() + "\r\n"
        return msg
    def __str__(self):
        return self.emit()

    def _checksum(self):
        msg = ','.join(str(f) for f in self.fields)[1:]
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
            port, #UART PortID
            00007, #inProto bitmask  (this should be a 2-bit mask, but it's 7 in the documentation's example, so I'm leaving it at 7.
            00003, #outProto bitmask
            baudrate, #baudrate
            0, # autobauding (0 or 1)
        ]

def read_UBX(device):
    def myread(n=1, label=''):
        x = device.read(n)
        if debug and len(x) > 0:
            print '[%.6f] %s (%s)' % (time.time(), ' '.join(['%02x' % ord(i) for i in x]), label)
        return x
    timeout_millis = 1000
    byteval = ''
    t0 = datetime.now()
    while byteval != '\xb5':
        dt = datetime.now() - t0
        if dt.seconds * 1000 + dt.microseconds / 1000 > timeout_millis:
            return None
        byteval = myread()
    msg = byteval
    msg += myread()
    assert msg[-1] == '\x62' # second sync byte
    msg_id = myread(2) # msg class and ID
    msg += msg_id
    payload_length_bytes = myread(2)
    msg += payload_length_bytes
    payload_length = struct.unpack('<h', payload_length_bytes)[0]
    payload = ''
    for i in range(payload_length):
        payload += myread()
    msg += payload
    msg += myread(2) # checksum bytes
    m = UBXMessage('','')
    m.msgid = msg_id
    m.payload = payload
    return m


def send(msg, baudrate=9600):
    #p = open(serial_device, 'wb')
    s = serial.Serial(serial_device, baudrate=baudrate)
    msgstr = msg.emit()
    print "Sending: " + msgstr
    s.write(msgstr)
    output = (read_UBX(s),read_UBX(s))
    if output[0] or output[1]:
        print "Got response: " + str(output)
    s.close()
    return output
    
def save(msg, filename):
    f = open(filename, 'wb')
    f.write(msg.emit())
    f.close()


if __name__ == '__main__':
    m = NMEA_SetRateMsg('GLL',0)
    print m.emit()
