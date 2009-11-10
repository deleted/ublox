#!/usr/bin/env python
import struct

serial_device = '/dev/cu.usbserial-A900adpX'

msgtypes = {
    'GLL': b'\xf0\x01',
    'RMC': b'\xf0\x04',
    'GSV': b'\xf0\x03',
}

commands = {
    'CFG-MSG': b'\x06\x01',
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
        msg += self._checksum(msg[2:]) # slice out the sync bytes
        return msg

    def _checksum(self, msg):
        ck_a = 0x00
        ck_b = 0x00
        b = buffer(msg)
        for i in b:
            ck_a += ord(i)
            ck_b += ck_a
        return struct.pack('bb', ck_a, ck_b)

class ConfigMessage(UBXMessage):
    def __init__(self, msgtype):
        payload = msgtypes[msgtype]
        command = 'CFG-MSG'
        UBXMessage.__init__(self, command, payload)

class NMEA_Message(object):
    """ Base class for NMEA Messages """
    def __init__(self, msgtype, rate):
        self.fields = []

    def emit(self):
        msg = ','.join(self.fields) + "\r\n"
        msg += self.checksum()
        return msg

    def _checksum(self):
        msg = ','.join(self.fields)[1:]
        checksum = 0
        for char in bytes(msg):
            checksum ^= ord(char)
        print "Checksum of %s is %s" % (msg, hex(checksum))
        return "*" + hex(checksum)[-2:].upper()

class NMEA_SetRateMsg(object):
    def __init__(self, msgtype, rate):
        self.fields = []
        self.fields.append('$PUBX')
        self.fields.append('40')
        self.fields.append(msgtype)
        for i in range(5):
            self.fields.append(str(rate))
        self.fields.append(str(0))

def send(msg):
    p = open(serial_device, 'wb')
    p.write(msg.emit())
    p.close()
