import numpy as np

from tecplot_tools.hdf import create_hdf5

x = np.linspace(0, 40, 41)
y = np.linspace(0, 10, 21)
z = np.linspace(0, 5, 7)
u = np.ones((7, 21, 41))
v = np.ones((7, 21, 41))
w = np.ones((7, 21, 41))

for i in range(len(z)):
    for j in range(len(y)):
        v[i, j, :] = np.sin(x)
for i in range(len(z)):
    for j in range(len(y)):
        w[i, j, :] = np.cos(x)
zz, yy, xx = np.meshgrid(z, y, x, indexing='ij')

create_hdf5('test.hdf', variables=dict(X=xx, Y=yy, Z=zz, x_velocity=u, y_velocity=v, z_velocity=w), taxis=None)
