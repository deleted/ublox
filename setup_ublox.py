import message

OLDBAUD = 9600
NEWBAUD = 4800

print "Setting NAV5 config to airborne mode..."
navconfig = message.UBXMessage('CFG-NAV5', "\x01\x00\x07\x03\x00\x00\x00\x00\x10'\x00\x00\x05\x00\xfa\x00\xfa\x00d\x00,\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00")
(ack, null) = message.send(navconfig, baudrate=OLDBAUD)
if ack:
    print "ACK: ", ack.emit()
else:
    print "Didn't get ACK."

print "\nSetting GLL message rate to 0.."
glloff = message.NMEA_SetRateMsg('GLL', 0)
message.send(glloff, baudrate=OLDBAUD)
print "Done." # NMEA messages don't get ACK'd

print "\nSetting NEWBAUD rate to %d..." % NEWBAUD
print "Port 1"
setbaudmsg = message.NMEA_SetBaudMessage(1, NEWBAUD)
message.send(setbaudmsg, OLDBAUD)
print "Port 2"
setbaudmsg = message.NMEA_SetBaudMessage(2, NEWBAUD)
message.send(setbaudmsg, baudrate=OLDBAUD)
print "Done."

print "\nSaving settings to flash..."
(ack, null) = message.send(message.UBXSaveConfig(), OLDBAUD)
(ack, null) = message.send(message.UBXSaveConfig(), NEWBAUD)
if ack:
    print "ACK: ", ack.emit()
else:
    print "Didn't get ACK."
    
print "Verifying NAV settings..."
(settings, ack) = message.send(message.UBXPollNav5(), NEWBAUD)
print "New settings: ", settings.payload
