import cv2
from pylibdmtx import pylibdmtx
from playsound import playsound


old_moduleName = ''
old_DNP = ''

IsScanned = '../Resource/IsScanned.mp3'

def ManualInput(name):
    NAME = input('Введите NAME: ')
    if len(NAME)==0:
         NAME = name['Name']
    DNP  = input('Введите DNP: ')
    if len(DNP)==0:
         DNP = name['DNP']
    SN   = input('ВВедите SN: ')
    print(NAME+','+DNP+','+SN)
    return { "Name": NAME, "DNP": DNP, "SN": SN }


def ScanDataMatrix(name):
    global old_moduleName,old_moduleDNP
    # get the webcam:  
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

    cap.set(3,320)
    cap.set(4,240)

    font = cv2.FONT_HERSHEY_SIMPLEX

    if cap.isOpened() != True:
        quit("Камера не найдена")

    while (cap.isOpened()):
        # Capture frame-by-frame
        ret, frame = cap.read()
        # Our operations on the frame come here
        #im = imutils.resize(frame, width=240)
        im = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
         
        decodedObjects = pylibdmtx.decode(im)
        for decodedObject in decodedObjects: 
            (x, y, w, h) = decodedObject.rect
            y = 240 - y
            cv2.rectangle(frame, (x, y), (x + w, y - h), (0, 0, 255), 2)

            barCode = decodedObject.data.decode('utf-8')
            cv2.putText(frame, barCode, (x, y-h), font, 0.5, (255,0,0), 1, cv2.LINE_AA)
            if barCode.find(name) >= 0:
                cap.release()
                cv2.destroyAllWindows()
                #print(barCode)
                lines = barCode.split(',')
                #playsound(IsScanned)
                print()
                return { "Name": lines[0], "DNP": lines[1], "SN": lines[2] }

               
        # Display the resulting frame
        cv2.imshow(name, frame)
        key = cv2.waitKey(1)
        if key & 0xFF == 27:
            break
        elif key & 0xFF == ord('m'): #m
              cap.release()
              cv2.destroyAllWindows()
              return ManualInput({"Name":old_moduleName,"DNP":old_DNP})
             

    # When everything done, release the capture
    cap.release()
    cv2.destroyAllWindows()
    quit("Нажато ESC")
