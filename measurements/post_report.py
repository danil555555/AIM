# -*- coding: cp1251 -*-
import paramiko

def post_report(filename):
      ssh= paramiko.SSHClient()
      ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
      ssh.connect(hostname='orion',username="stend",password="stendFTPWrite")
      ftp=ssh.open_sftp()
      #ftp.chdir('pub/Devices/CTD-1620/'+modulename)
      ftp.put(filename,'/srv/ftp/pub/Devices/CTD-1620/'+filename)


 