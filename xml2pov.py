from sys import argv

import numpy as np

from .XmlReader import Xml


# import re


def pbc(r, d):
    return r - d * np.round(r / d)


top = Xml(argv[1])
n_atoms = top.meta['natoms']
type_array = top.contents.get('type')
if type_array is not None:
    types = list(set(type_array))
else:
    types = ['A']

color_dict = {}
radius_dict = {}

# for t in types:
#    color = input("Enter color vector for type %s: " % t)
#    color_dict[t] = np.asarray(re.split('\s+|,\s*', color), dtype=np.float)
#    radius = float(input("Enter color vector for type %s: " % t))
#    radius_dict[t] = radius

radius_dict['A'] = 0.4
radius_dict['B'] = 0.2
radius_dict['C'] = 0.2
color_dict['A'] = np.array([0.972549, 0.176471, 0.176471, 0])
# color_dict['B'] = np.array([0.584314, 0.921569, 0, 0])
color_dict['B'] = np.array([0.254902, 0.654902, 1, 0])
color_dict['C'] = np.array([0.254902, 0.654902, 1, 0])

bonds = top.contents.get('bond')
if bonds is None:
    bonds = []
    bond_types = ['bond']
else:
    bond_types = list(set(bonds[:, 0]))

bond_r_dict = {}
# for t in bond_types:
#    radius = float(input("Enter color vector for bond %s: " % t))
#    bond_r_dict[t] = radius
bond_r_dict['polymer'] = 0.2
bond_r_dict['graft'] = 0.2

# do not modify
head = '''
#version 3.5;
#include "transforms.inc"
'''
ray_tracing = '''
global_settings {
radiosity {
count 128
always_sample on
recursion_limit 4
error_bound 0.8
}
}
'''
# Generate a pov file from ovito or vmd, choose light source and view point. THEN MODIFY HERE.
view = '''
background { color rgb <1, 1, 1>}
sphere { <-9.91821e-05, 0, -9.91821e-05>, 1463.3
         texture {
             pigment { color rgb 1.0 }
             finish { emission 0.8 }
         }
         no_image
         no_shadow
}
camera {
  orthographic
  location <0, 77.1263, 0>
  direction <0, -38.5632, 0>
  right <126.278, 0, 0>
  up <0, 0, 94.7083>
  sky <0, 0, 94.7083>
  look_at <0, 38.5632, 0>
  Axis_Rotate_Trans(<-1, 0, 0>, 90)
  translate <2.36031, -0.738633, -9.91821e-05>
}
light_source {
  <0, 0, 0>
  color <0.25, 0.25, 0.25>
  shadowless
  parallel
  point_at <0, 0, 1>
}
'''
# do not modify
macro = '''
#macro SPRTCLE(pos, particleRadius, particleColor) // Macro for spherical particles
sphere { pos, particleRadius
         texture { pigment { color particleColor } }
}
#end
#macro DPRTCLE(pos, particleRadius, particleColor) // Macro for flat disc particles facing the camera
disc { pos, <0, 0, -1>, particleRadius
         texture { pigment { color particleColor } }
}
#end
#macro CPRTCLE(pos, particleRadius, particleColor) // Macro for cubic particles
box { pos - <particleRadius,particleRadius,particleRadius>, pos + <particleRadius,particleRadius,particleRadius>
         texture { pigment { color particleColor } }
}
#end
#macro SQPRTCLE(pos, particleRadius, particleColor) // Macro for flat square particles facing the camera
triangle { pos+<1, 1, 0>*particleRadius, pos+<1, -1, 0>*particleRadius, pos+<-1, -1, 0>*particleRadius
         texture { pigment { color particleColor } }
}
triangle { pos+<1, 1, 0>*particleRadius, pos+<-1, -1, 0>*particleRadius, pos+<-1, 1, 0>*particleRadius
         texture { pigment { color particleColor } }
}
#end
#macro CYL(base, dir, cylRadius, cylColor) // Macro for cylinders
cylinder { base, base + dir, cylRadius
         texture { pigment { color cylColor } }
}
#end
'''

header = head + ray_tracing + view + macro

colors = ''
for t in types:
    colors += '#declare type_%s = rgbt <%.6f,%.6f,%.6f,%.6f>;\n' % (t, *tuple(color_dict[t]))

for f in argv[1:]:
    out_put = open('/home/shirui/pic-2021-06-03/' + f.replace('.xml', '.pov').replace('../', ''), 'w')
    out_put.write(header)
    out_put.write(colors)
    xml = Xml(f, needed=['position'])
    pos = xml.contents['position']
    box = np.asarray([xml.box.lx, xml.box.ly, xml.box.lz], dtype=np.float64)
    if type_array is None:
        type_array = ['A'] * n_atoms
    for p, t in zip(pos, type_array):
        out_put.write('SPRTCLE(<%.6f, %.6f, %.6f>, %.6f, type_%s)\n' % (*tuple(p), radius_dict[t], t))
    for b in bonds:
        pa = pos[int(b[1])]
        pb = pos[int(b[2])]
        dr_a = pbc(pb - pa, box)
        r_ba = pa + dr_a
        is_dr_a = not np.isclose(r_ba, box / 2, atol=0.001).any()
        if is_dr_a:
            ratio = 1
            r = r_ba / (box / 2)
            if (np.abs(r) > 1.0).any():
                ratio = r[np.argmax(np.abs(r))]
            r_ba = r_ba / ratio
            dr_a = r_ba - pa
            out_put.write('CYL(<%.6f, %.6f, %.6f>, <%.6f, %.6f, %.6f>, %.4f, type_%s)\n' %
                          (*tuple(pa), *tuple(dr_a), bond_r_dict[b[0]], type_array[int(b[1])]))
        dr_b = pbc(pa - pb, box)
        r_ab = pb + dr_b
        is_dr_b = not np.isclose(r_ab, box / 2, atol=0.001).any()
        if is_dr_b:
            ratio = 1
            r = r_ab / (box / 2)
            if (np.abs(r) > 1.0).any():
                ratio = r[np.argmax(np.abs(r))]
            r_ab = r_ab / ratio
            dr_b = r_ab - pb
            out_put.write('CYL(<%.6f, %.6f, %.6f>, <%.6f, %.6f, %.6f>, %.4f, type_%s)\n' %
                          (*tuple(pb), *tuple(dr_b), bond_r_dict[b[0]], type_array[int(b[2])]))
    out_put.close()
