import os
paths = [
    r'C:\Program Files (x86)\Steam\steamapps\common\Grand Theft Auto San Andreas',
    r'C:\Program Files (x86)\Steam\steamapps\common\Grand Theft Auto III',
    r'C:\Program Files (x86)\Steam\steamapps\common\Grand Theft Auto Vice City',
    r'C:\Program Files (x86)\Steam\steamapps\common\Grand Theft Auto IV\GTAIV',
    r'C:\Program Files (x86)\Steam\steamapps\common\Max Payne 3\Max Payne 3',
]
for p in paths:
    print('----', p, '----')
    if os.path.isdir(p):
        exes = sorted([n for n in os.listdir(p) if n.lower().endswith('.exe')])
        for name in exes:
            print('  ', name)
        cmdline = os.path.join(p, '@commandline.txt')
        print('  @commandline.txt:', 'FOUND' if os.path.isfile(cmdline) else 'MISSING')
    else:
        print('  MISSING')
