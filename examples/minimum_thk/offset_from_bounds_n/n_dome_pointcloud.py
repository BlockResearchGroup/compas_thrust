import os
import compas_tno
from compas_tno.diagrams import FormDiagram
from compas_tno.shapes import Shape
from compas_tno.optimisers import Optimiser
from compas_tno.plotters import plot_form
from compas_tno.analysis import Analysis
from compas_tno.viewers import view_shapes
from compas_tno.viewers import view_shapes_pointcloud
from compas_tno.viewers import view_solution
from compas_tno.shapes import MeshDos
import math
from scipy import rand

# ----------------------------------------------------------------------
# ----------- EXAMPLE OF MIN THRUST FOR DOME WITH RADIAL  FD -----------
# ----------------------------------------------------------------------

# Basic parameters

thk = 0.5
radius = 5.0
type_structure = 'dome'
type_formdiagram = 'radial_spaced_fd'
# type_formdiagram = 'radial_fd'
discretisation = [8, 20]
center = [5.0, 5.0]
gradients = False
n = 4
error = 0.10
ro = 1.0

# ----------------------- Shape Analytical ---------------------------

data_shape = {
    'type': type_structure,
    'thk': thk,
    'discretisation': [discretisation[0]*n, discretisation[1]*n],
    'center': center,
    'radius': radius,
    't': 0.0
}

analytical_shape = Shape.from_library(data_shape)
analytical_shape.ro = ro
area_analytical = analytical_shape.middle.area()
swt_analytical = analytical_shape.compute_selfweight()

print('Analytical Self-weight is:', swt_analytical)
print('Analytical Area is:', area_analytical)

# ----------------------- Point Cloud -----------------------

xy = []
points_ub = []
points_lb = []
xc = center[0]
yc = center[1]
n_radial = discretisation[0] * n
n_spikes = discretisation[1] * n
r_div = radius/n_radial
theta = 2*math.pi/n_spikes

for nr in range(n_radial+1):
    for nc in range(n_spikes):
        xi = xc + nr * r_div * math.cos(theta * nc)
        yi = yc + nr * r_div * math.sin(theta * nc)
        xy.append([xi, yi])

z_ub = analytical_shape.get_ub_pattern(xy).reshape(-1, 1) + error * (2 * rand(len(xy), 1) - 1)
z_lb = analytical_shape.get_lb_pattern(xy).reshape(-1, 1) + error * (2 * rand(len(xy), 1) - 1)

for i in range(len(xy)):
    points_lb.append([xy[i][0], xy[i][1], float(z_lb[i])])
    points_ub.append([xy[i][0], xy[i][1], float(z_ub[i])])

# # triangulated_shape = Shape.from_pointcloud(points_lb, points_ub)
# view_shapes_pointcloud(triangulated_shape).show()

# ----------------------- Form Diagram ---------------------------

data_diagram = {
    'type': type_formdiagram,
    'center': [5.0, 5.0],
    'radius': radius,
    'discretisation': discretisation,
    'r_oculus': 0.0,
    'diagonal': False,
    'partial_diagonal': False,
}

form = FormDiagram.from_library(data_diagram)
print('Form Diagram Created!')
plot_form(form, show_q=False, fix_width=False).show()

# ------- Create shape given a topology and a point cloud --------

triangulated_shape = Shape.from_pointcloud(points_lb, points_ub)
view_shapes_pointcloud(triangulated_shape).show()

vault = Shape.from_pointcloud_and_formdiagram(form, points_lb, points_ub, middle=analytical_shape.middle, data={'type': 'general', 't': 0.0, 'thk': thk})
vault.store_normals()
vault.ro = ro

area = vault.middle.area()
swt = vault.compute_selfweight()

print('Interpolated Volume Data:')
print('Self-weight is: {0:.2f} diff ({1:.2f}%)'.format(swt, 100*(swt - swt_analytical)/(swt_analytical)))
print('Area is: {0:.2f} diff ({1:.2f}%)'.format(area, 100*(area - area_analytical)/(area_analytical)))

# view_shapes(vault).show()
# view_shapes_pointcloud(vault).show()

form.selfweight_from_shape(vault)
# view_shapes(vault).show()

# --------------------- 3. Create Starting point with TNA ---------------------

# form = form.initialise_tna(plot=False)
form.initialise_loadpath()
# plot_form(form).show()

# --------------------- 4. Create Minimisation Optimiser ---------------------

optimiser = Optimiser()
optimiser.settings['library'] = 'Scipy'
optimiser.settings['solver'] = 'SLSQP'
optimiser.settings['constraints'] = ['funicular', 'envelope', 'reac_bounds']
optimiser.settings['variables'] = ['ind', 'zb', 'n']
optimiser.settings['objective'] = 'n'
optimiser.settings['printout'] = True
optimiser.settings['plot'] = False
optimiser.settings['find_inds'] = True
optimiser.settings['qmax'] = 1000.0
optimiser.settings['gradient'] = gradients
optimiser.settings['jacobian'] = gradients

# --------------------- 5. Set up and run analysis ---------------------

analysis = Analysis.from_elements(vault, form, optimiser)
analysis.apply_selfweight()
analysis.apply_envelope()
analysis.apply_reaction_bounds()
analysis.set_up_optimiser()
analysis.run()

n_reduction = -1 * analysis.optimiser.fopt
thk_min = thk - 2*n_reduction*thk
print('Approx. Minimum THK:', thk_min)
data_shape['thk'] = thk_min

plot_form(form, show_q=False, cracks=True).show()

# analytical_shape = Shape.from_library(data_shape)
# form.envelope_from_shape(analytical_shape)

# plot_form(form, show_q=False, cracks=True).show()

form.to_json(compas_tno.get('test.json'))

view_solution(form, vault).show()
