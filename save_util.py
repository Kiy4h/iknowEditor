#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from gettext import gettext as _


def save(l):
    home_dir = os.path.expanduser('~')
    f = open(home_dir + '/salida.py', 'w')
    # encabezados
    f.write("# -*- coding: utf-8 -*-\n")
    f.write("\n")
    f.write("from gettext import gettext as _\n")
    f.write("\n")
    f.write("NAME = _('Place')\n")
    f.write("\n")
    f.write("STATES = []\n")
    f.write("\n")
    f.write("CITIES = [\n")
    first = True
    for r in l:
        #    (_('name'), x, y, type, dx, dy),
        if first:
            first = False
        else:
            f.write(',\n')
        
        lin = "    (_('" + str(r[0]) + "'), " + str(r[1]) + ", " + str(r[2])
        lin = lin + ", 2, " + str(r[3]) + ", " + str(r[4]) + ")"

        f.write(lin)
    f.write('\n')
    f.write(']')
    f.close()


def fixValues(data, scale, shift_x, shift_y):
    l = []
    for e in data:
        name = e[0]
        pos_x = int((e[1] - shift_x) / scale)
        pos_y = int((e[2] - shift_y) / scale)
        dx = e[3]
        dy = e[4]
        l.append((name, pos_x, pos_y, dx, dy))
    return l
