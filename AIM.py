class Aim:

    def __init__(self, name, dnp, sn, ctd1620):

        self.name = name
        self.module_type = name[0:3]
        self.cannels = int(self.name.split("-")[1][0])
        self.dnp = dnp
        self.sn = sn
        self.ctd1620 = ctd1620
        
    




    