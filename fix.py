import os
import sys

filename = 'resume.pdf'

size = os.stat(filename).st_size

pad = 0
while (size+pad) % 2048 != 0:
    pad += 1

with open(filename,'r+b') as f:
    f.seek(size)
    f.write('\x00'*pad)




