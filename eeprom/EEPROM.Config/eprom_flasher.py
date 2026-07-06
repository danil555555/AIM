#!/usr/bin/python3
# -*- coding: utf-8 -*-
import datetime
import struct,sys,socket,time
if len(sys.argv) < 6:
   print('Usage: '+sys.argv[0]+' st1620_IP r | w slot_type slot_number record_number [file_name] [serial_number]')
   sys.exit(0)

IP = sys.argv[1]
RW = sys.argv[2]
slotType     = int(sys.argv[3]) # Тип разъема 0- Аналоговый 1- Слот расширения 2- Кросс плата
slotNumber   = int(sys.argv[4]) # Номер разъема, начиная с 0
recordNumber = int(sys.argv[5]) # Номер записи. Если в плате нет записи с номером на единицу меньшим, то запись будет неуспешной.
                                # Первая запись имеет нулевой номер. Размер записи ограничен 1024 байтами.
                                # Все записи с номерами большими чем записанный будут удалены
fileName     = ''
serialNumber = 0

if len(sys.argv) >= 7:
   fileName = sys.argv[6]

if len(sys.argv) >= 8:
   serialNumber = int(sys.argv[7])

sock = socket.socket()
if RW == 'r':
   sock.connect((IP, 30001))
   getrec = struct.pack('<4sl4slll', str.encode('SND>'), 16, str.encode('GTRC'), slotType, slotNumber, recordNumber)
   sock.send(getrec)
   time.sleep(0.1)
   ansv = sock.recv(2048)
   anst = struct.unpack('<4sl'+str(len(ansv)-8)+'s', ansv)
   if fileName != '':
       outfile = open(fileName, 'wb')
       data = outfile.write(anst[2])
       outfile.close()
   else:
       sys.stdout.write(anst[2].decode('CP1251'))
   sock.close()
   exit(0)

if RW == 'w':
   sock.connect((IP, 30001))
   if fileName != '':
       infile = open(fileName, 'rb')
       data = infile.read()
       infile.close()
   else:
       data = sys.stdin.read()
   datalen = len(data)
   if (datalen % 4) != 0:
      datalen += (4 - (datalen % 4))
      data = data.ljust(datalen,'\0')

   # Заменим дату на текущую
   index = data.find(str.encode('DATE'))
   if index >= 0:
       date = datetime.date.today().strftime("%d.%m.%Y")
       serl_old = data[index:index+18]
       serl_new = struct.pack('<4sl10s', str.encode('DATE'), 3, str.encode(date))
       data = data.replace(serl_old, serl_new)

   # Замена серийного номера
   if serialNumber > 0:
       index = data.find(str.encode('SERL'))
       if index >= 0:
           serl_old = data[index:index+12]
           serl_new = struct.pack('<4sll', str.encode('SERL'), 1, serialNumber)
           data = data.replace(serl_old, serl_new)

   burnrec = struct.pack('<4sl4sllll'+str(len(data))+'s', str.encode('SND>'), 20+datalen, str.encode('BRRC'), slotType, slotNumber, recordNumber, datalen, data)
   sock.send(burnrec)
   time.sleep(1)
   ansv = sock.recv(2048)
   anst = struct.unpack('<4sl'+str(len(ansv)-8)+'s', ansv)
   print(anst[2].decode('CP1251'))
   sock.close()
   exit(0)

print('Error: Unknow parameter')
