#!/usr/bin/python
#  coding: utf-8
import struct, sys
#On Windows use option -u

if len(sys.argv) != 2:
    print('Usage: python record_gen.py <config.txt>')
    print('Output: file <config.bin>')
    exit(0)

filename = sys.argv[1]
infile = open(filename, 'r')

conf_str = ''
for instr in infile:
    instr = instr.strip()
    if len(instr) == 0:
       continue

    instr = instr.replace('[','') # Убираем скобки
    instr = instr.replace(']','')

    instr_spl = instr.split('#')
    instr = instr_spl[0]
    instr_spl = instr.split(',')

    if instr_spl[0] == 'CALB':
       instr_spl = instr.split(',')
       if (len(instr_spl) % 2) != 0 or instr_spl[1][0] != '\'' or instr_spl[1][len(instr_spl[1])-1] != '\'':
          sys.stderr.write('Incorrect data for CALB tag')
          sys.exit(-1)

       datelen = len(instr_spl[1])-2
       if (datelen % 4) != 0:
           fill = ' '*(4 - (datelen % 4))
           instr_spl[1] = instr_spl[1][1:datelen+1]
           instr_spl[1] += fill
           instr_spl[1] = '\''+instr_spl[1]+'\''
       chancnt = (len(instr_spl)-2)/2
       instr_spl.insert(1, str(datelen))
       instr_spl.insert(3, str(chancnt))

    if instr_spl[0] == 'ECNF':
       instr_spl = instr.split(',')
       if ((len(instr_spl)-4) % 3) != 0 or instr_spl[2][0] != '\'' or instr_spl[2][len(instr_spl[2])-1] != '\'':
          sys.stderr.write('Incorrect data for ECNF tag')
          sys.exit(-1)

       if instr_spl[3][0] != '\'' or instr_spl[3][len(instr_spl[3])-1] != '\'':
          sys.stderr.write('Incorrect data for ECNF tag')
          sys.exit(-1)

       datalen = len(instr_spl[2])-2
       if (datalen % 4) != 0:
           fill = ' '*(4 - (datalen % 4))
           instr_spl[2] = instr_spl[2][1:datalen+1]
           instr_spl[2] += fill
           instr_spl[2] = '\''+instr_spl[2]+'\''
           datalen+=len(fill)
       instr_spl.insert(2, str(datalen/4))

       datalen = len(instr_spl[4])-2
       if (datalen % 4) != 0:
           fill = ' '*(4 - (datalen % 4))
           instr_spl[4] = instr_spl[4][1:datalen+1]
           instr_spl[4] += fill
           instr_spl[4] = '\''+instr_spl[4]+'\''
           datalen+=len(fill)
       instr_spl.insert(4, str(datalen/4))
       chancnt = (len(instr_spl)-6)
       instr_spl.insert(6, str(chancnt))

    instr = ''
    instr_spl[0] = '\'' + instr_spl[0]+'\''
    for isp in instr_spl:
        instr += (isp+',')

    instr = instr[0:len(instr)-1]
    conf_str += ('['+instr)
    conf_str += '],'
conf_str = '[' + conf_str
conf_str = conf_str[0:len(conf_str)-1] + ']'
conf = eval(conf_str)
record_size = 0
for tag in conf:
   if not type(tag) is list:
       sys.stderr.write('No data for tag')
       sys.exit(0)

   if (not type(tag[0]) is str) or len(tag[0]) != 4:
       sys.stderr.write('Incorrect tag id')
       sys.exit(0)

   tag_size = 0
   for param in tag:
      if type(param) is int:
          tag_size += 4
      elif type(param) is str:
          tag_size += len(param)
      elif type(param) is float:
          tag_size += 4
      else:
          sys.stderr.write('Incorrect data')
          sys.exit(0)

   record_size += tag_size
   tag_size -= 4 # Имя тега не входит в размер тега
   if (tag_size % 4) != 0: # Вставляем нули для кратности размера 4 
       tag.insert(len(tag), ''.ljust((4- (tag_size % 4)), '\0'))
       record_size += (4-(tag_size % 4))
       tag_size += (4-(tag_size % 4))
   tag.insert(1, tag_size//4) # Вставляем размер в 4 байтных словах
   record_size += 4 

infile.close()

if record_size >= 1024:
   sys.stderr.write('Record too big. Separate it into multiple records')
   sys.exit(-1)

filename = sys.argv[1].replace('.txt', '.bin')
outfile = open(filename, 'wb')

for tag in conf:
   for param in tag:
       format = '<'
       if type(param) is str:
          format += (str(len(param))+'s')
          bstr = struct.pack(format, str.encode(param))
       elif type(param) is int:
          format += 'l'
          bstr = struct.pack(format, param)
       elif type(param) is float:
          format += 'f'
          bstr = struct.pack(format, param)
       else:
          print('Error: Unknown type')

       outfile.write(bstr)

outfile.close()
