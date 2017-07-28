import os, time
import subprocess

def wifi_test():
  cmd='iwinfo ra0 scan'
  cmd_split=cmd.split()

  out = subprocess.Popen(cmd_split, stdout=subprocess.PIPE).communicate()
  # print out[0]
  if 'Cell 01 - Address' in out[0]:
    # print 'find louter'
    return True
  else:
    return False
    # connect louter and ping once
      

if __name__=='__main__':
    wifi_test()