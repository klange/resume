#!/usr/bin/env python3.6
import datetime
import os
import subprocess

hashtypes = ['md5','sha256','sha512']
sums = {x:subprocess.check_output([f"{x}sum",'resume.pdf']).decode('utf-8').split()[0] for x in hashtypes}

#with open('/home/klange/Projects/resume-iso/util/cdrom/boot/grub/theme.txt','r') as f:
#    theme = f.read()
#    r = theme.find('résumé')
#    q = theme.find('"',r)
#    version = theme[r+7:q]
version = 'built from ToaruOS 1.10.1'

date = datetime.datetime.now().date().isoformat()

hashes = "\n".join(f"{x}: {sums[x]}" for x in hashtypes)

data = f"{date} ({version})\n{hashes}"

size = int(round(os.path.getsize('resume.pdf') / 1048576))


variables = {
    'LATEST_RELEASE': data,
    'SIZE': size,
}

with open('template.htm','r') as f:
    template = f.read()
    for k in variables:
        template = template.replace(f'%%{k}%%', str(variables[k]))

    with open('index.htm','w') as out:
        out.write(template)
