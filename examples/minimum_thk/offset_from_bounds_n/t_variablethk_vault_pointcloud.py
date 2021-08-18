import os
import compas_tno
from compas_tno.diagrams import FormDiagram
from compas_tno.shapes import Shape
from compas_tno.optimisers import Optimiser
from compas_tno.plotters import plot_form
from compas_tno.analysis import Analysis
from compas_tno.viewers import view_shapes
from compas_tno.viewers import view_normals
from compas_tno.viewers import view_shapes_pointcloud
from compas_tno.viewers import view_solution
import json
from scipy import rand
from compas_tno.viewers import view_mesh
from numpy import array


# ----------------------------------------------------------------------
# ----------- EXAMPLE OF MIN THRUST FOR DOME WITH RADIAL  FD -----------
# ----------------------------------------------------------------------

# Basic parameters

thk = 0.5
error = 0.0
span = 10.0
k = 1.0
n = 2
type_structure = 'crossvault'
type_formdiagram = 'cross_fd'
discretisation = 10
thickness_type = 'variable'
gradients = True  # False

# ----------------------- Point Cloud -----------------------

file_name = 'nurbs1'
# file_name = 'amiens'
pointcloud = '/Users/mricardo/compas_dev/me/min_thk/pointcloud/' + file_name + '.json'

points_ub = []
points_lb = []
xy_span = [[0, span], [0, k*span]]

tol = 10e-4

with open(pointcloud) as json_file:
    data = json.load(json_file)
    for key, pt in data['UB'].items():
        if abs(pt[0] - 0.0) < tol:
            pt[0] = 0.0
        if abs(pt[0] - span) < tol:
            pt[0] = span
        if abs(pt[1] - 0.0) < tol:
            pt[1] = 0.0
        if abs(pt[1] - span) < tol:
            pt[1] = span
        points_ub.append(pt)
    for key, pt in data['LB'].items():
        points_lb.append(pt)

triangulated_shape = Shape.from_pointcloud(points_lb, points_ub)
# view_shapes_pointcloud(triangulated_shape).show()

# ----------------------- Form Diagram ---------------------------

data_diagram = {
    'type': type_formdiagram,
    'xy_span': xy_span,
    'discretisation': discretisation,
    'fix': 'corners',
}

form = FormDiagram.from_library(data_diagram)
print('Form Diagram Created!')
# plot_form(form, show_q=False, fix_width=False).show()

# ------- Create shape given a topology and a point cloud --------

# roots - not considering real middle
# vault = Shape.from_pointcloud_and_formdiagram(form, points_lb, points_ub)
# more improved, considers the real middle
vault = Shape.from_pointcloud_and_formdiagram(form, points_lb, points_ub, data={'type': 'general', 't': 0.0, 'thk': thk})

# --------------------
# Mesh as a percentage
# --------------------

zub = array(vault.intrados.vertices_attributes('z'))
zlb = array(vault.extrados.vertices_attributes('z'))
vault.middle.store_normals()
vault.middle.scale_normals_with_ub_lb(zub, zlb)
vault.data['thickness_type'] = thickness_type

area = vault.middle.area()
swt = vault.compute_selfweight()

print('Interpolated Volume Data:')
print('Self-weight is: {0:.2f}'.format(swt))
print('Area is: {0:.2f}'.format(area))

# view_shapes(vault).show()

form.selfweight_from_shape(vault)
# form.selfweight_from_shape(analytical_shape)

# --------------------- 3. Create Starting point with TNA ---------------------

# form = form.initialise_tna(plot=False)
form.initialise_loadpath()
# plot_form(form).show()

# --------------------- 4. Create Minimisation Optimiser ---------------------

optimiser = Optimiser()
optimiser.settings['library'] = 'Scipy'
optimiser.settings['solver'] = 'SLSQP'
optimiser.settings['constraints'] = ['funicular', 'envelope']
optimiser.settings['variables'] = ['ind', 'zb', 't']
optimiser.settings['objective'] = 't'
optimiser.settings['thickness_type'] = thickness_type
optimiser.settings['min_thk'] = 0.0
optimiser.settings['max_thk'] = 2.0
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

plot_form(form, show_q=False, cracks=True).show()

# analytical_shape = Shape.from_library(data_shape)
# form.envelope_from_shape(analytical_shape)

# plot_form(form, show_q=False, cracks=True).show()

form.to_json(compas_tno.get('test.json'))

view_solution(form, vault).show()
