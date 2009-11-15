import message


print "Setting NAV5 config to airborne mode..."
navconfig = message.UBXMessage('CFG-NAV5', "\x01\x00\x07\x03\x00\x00\x00\x00\x10'\x00\x00\x05\x00\xfa\x00\xfa\x00d\x00,\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00")
(ack, null) = message.send(navconfig)
if ack:
    print "ACK: ", ack.emit()
else:
    print "Didn't get ACK."

print "\nSetting GLL message rate to 0.."
glloff = message.NMEA_SetRateMsg('GLL', 0)
message.send(glloff)
print "Done." # NMEA messages don't get ACK'd

print "\nSaving settings to flash..."
(ack, null) = message.send(message.UBXSaveConfig())
if ack:
    print "ACK: ", ack.emit()
else:
    print "Didn't get ACK."
    
print "Verifying NAV settings..."
(settings, ack) = message.send(message.UBXPollNav5())
print "New settings: ", settings.payload