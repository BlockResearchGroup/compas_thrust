from compas_tna.diagrams import FormDiagram

from compas_thrust.algorithms.grad_based import optimise_tna
from compas_thrust.algorithms.scale import evaluate_scale
from compas_thrust.algorithms.scale import lagrangian_scale
from compas_thrust.algorithms.scale import scale_form
from compas_thrust.algorithms.equilibrium import z_from_form

from compas_thrust.diagrams.form import energy
from compas_thrust.diagrams.form import loadpath
from compas_thrust.diagrams.form import adapt_tna
from compas_thrust.diagrams.form import evaluate_a
from compas.geometry import Plane

from compas.numerical import grad

# from scipy import tensordot
# from scipy.optimize import nnls

from sympy import Array
from sympy import tensorproduct

from compas.numerical import normrow
from compas.numerical import normalizerow
from compas.geometry import normalize_vector
from compas.datastructures import mesh_face_matrix
from compas.datastructures import mesh_quads_to_triangles
from compas.geometry import is_ccw_xy

from compas.datastructures import Mesh
from compas_plotters import MeshPlotter

from compas_thrust.plotters.plotters import plot_form

from copy import deepcopy
from numpy import array
from numpy import argmin
from numpy import cross
from numpy import dot
from numpy import zeros
from numpy import int8
from numpy.linalg import lstsq
from numpy.linalg import matrix_rank
from numpy.linalg import pinv
from numpy.linalg import det

from compas.numerical.linalg import spsolve
from compas.numerical.linalg import spsolve_with_known
import math
from numpy.linalg import inv


__author__    = ['Ricardo Maia Avelino <mricardo@ethz.ch>']
__copyright__ = 'Copyright 2019, BLOCK Research Group - ETH Zurich'
__license__   = 'MIT License'
__email__     = 'mricardo@ethz.ch'


__all__ = [
    'planes_trimesh',
    'local_matrix',
    'local_matrix_external',
    'assembly_Cf',
    'A_heights',
    'A_stress',
    'hessian',
    'simple_nurbs'
]

def planes_trimesh(form):

    # Planes Of the Triangles

    for key in form.faces():
        vs = form.face_vertices(key)
        M.append(vs)
        p1 = array(form.vertex_coordinates(vs[0]))
        p2 = array(form.vertex_coordinates(vs[1]))
        p3 = array(form.vertex_coordinates(vs[2]))
        # print(p1,p2,p3)
        v1 = p3 - p1
        v2 = p2 - p1
        cp = cross(v1,v2)
        a, b, c = cp
        d = -1 * dot(cp, p3)
        sol = [a,b,c,d]
        form.set_face_attribute(key, 'dx', value=a/abs(a))
        form.set_face_attribute(key, 'dy', value=b/abs(b))

        # print('Sol:')
        # print(sol)
    
    return 

def local_matrix(form, key, plot=False):

    k_i = form.key_index()
    uv_i = form.uv_index()

    if plot:
        print('Internal -> key: {0} , index: {1}'.format(key,k_i[key]))

    neighbors = form.vertex_neighbors(key,ordered=True)

    if is_ccw_xy(form.vertex_coordinates(key), form.vertex_coordinates(neighbors[0]), form.vertex_coordinates(neighbors[1])) is True:
        pass
    else:
        neighbors.reverse()

    if plot:
        print('neighbors:', neighbors)
    i = 0

    hn = []
    kn = []
    ln = []

    uv_lg = {}
    k_lg = {}
    
    for v in neighbors:
        edge = array(form.vertex_coordinates(v)[:2] + [0]) - array(form.vertex_coordinates(key)[:2] + [0])
        hi = cross(edge, [0,0,1])
        hn.append(normalize_vector(hi)[:2])
        ln.append(normrow(edge))
        kn.append(normalize_vector(edge)[:2])
        try:
            i_edge = uv_i[(v,key)]
        except:
            i_edge = uv_i[(key,v)]
        uv_lg[i] = i_edge
        k_lg[i] = k_i[v]
        i += 1
    
    k_lg[i] = k_i[key]

    pn = len(neighbors)

    # local matrix

    j_= zeros((pn,pn+1), dtype=int8)
    j__ = zeros((pn,pn+1), dtype=int8)
    j___ = zeros((pn,pn+1), dtype=int8)

    for j in range(pn):
        for k in range(pn+1):
            j_[j][k] = j
            if j_[j][k] > 0:
                j__[j][k] = j_[j][k] - 1
            else:
                j__[j][k] = pn - 1
            if j_[j][k] < pn - 1:
                j___[j][k] = j_[j][k] + 1
            else:
                j___[j][k] = 0

    # print(j_)
    # print(j__)
    # print(j___)

    C = zeros((pn,pn+1))

    for j in range(pn):
        for k in range(pn+1):
            m = j_[j][k]
            n = j__[j][k]
            p = j___[j][k]
            C[j][k] = 0.0
            if k == m:
                C[j][k] = dot(hn[p],hn[m])/(ln[m] * dot(hn[p], kn[m])) - dot(hn[n],hn[m])/(ln[m] * dot(hn[n], kn[m]))
            if k == n:
                C[j][k] = -1 * dot(hn[m],hn[m])/(ln[n] * dot(hn[m], kn[n]))
            if k == p:
                C[j][k] = dot(hn[m],hn[m])/(ln[p] * dot(hn[m], kn[p]))
            if k == pn:
                C[j][k] = -1 * ( dot(hn[p],hn[m])/(ln[m] * dot(hn[p], kn[m])) - dot(hn[n],hn[m])/(ln[m] * dot(hn[n], kn[m])) ) -1 * (-1 * dot(hn[m],hn[m])/(ln[n] * dot(hn[m], kn[n])) ) -1 * ( dot(hn[m],hn[m])/(ln[p] * dot(hn[m], kn[p])) )

    # print('Local Matrix C int')
    # print(C.shape)
    # print(k_lg)
    # print(uv_lg)
    
    return C, k_lg, uv_lg

def local_matrix_external(form, key, plot = False):

    k_i = form.key_index()
    uv_i = form.uv_index()

    neighbors = form.vertex_neighbors(key,ordered=True)
    if is_ccw_xy(form.vertex_coordinates(key), form.vertex_coordinates(neighbors[0]), form.vertex_coordinates(neighbors[1])) is True:
        pass
    else:
        neighbors.reverse()
        if plot:
            print('Reversed Local Matrix')
    
    boundary = form.vertices_on_boundary()

    if plot:
        print('External -> key: {0} , index: {1}'.format(key,k_i[key]))

    # Shift list so it starts in the one in boundary

    if neighbors[0] not in boundary:
        if plot:
            print('Shift')
        for i in range(1,len(neighbors)):
            if neighbors[i] in boundary:
                neighbors = neighbors[i:] + neighbors[:i]

    if plot:
        print('neighbors:', neighbors)
    i = 0
    j = 0

    hn = []
    kn = []
    ln = []

    uv_lg = {}
    k_lg = {}
    
    for v in neighbors:
        edge = array(form.vertex_coordinates(v)[:2] + [0]) - array(form.vertex_coordinates(key)[:2] + [0])
        hi = cross(edge, [0,0,1])
        hn.append(normalize_vector(hi)[:2])
        ln.append(normrow(edge))
        kn.append(normalize_vector(edge)[:2])
        try:
            i_edge = uv_i[(v,key)]
        except:
            i_edge = uv_i[(key,v)]
        if form.is_edge_on_boundary(key,v) is False:
            uv_lg[j] = i_edge
            j +=1
        k_lg[i] = k_i[v]
        i += 1
    
    k_lg[i] = k_i[key]

    # quantity of neighbors in boundary
    nj = len(neighbors[1:len(neighbors)-1]) # in reality
    pn = len(neighbors)

    # local matrix

    j_= zeros((nj,pn+1), dtype=int8)
    j__ = zeros((nj,pn+1), dtype=int8)
    j___ = zeros((nj,pn+1), dtype=int8)

    for j in range(nj):
        for k in range(pn+1):
            j_[j][k] = j + 1
            j__[j][k] = j + 2
            j___[j][k] = j + 2

    # print(j_)
    # print(j__)
    # print(j___)

    C = zeros((nj,pn+1))

    for j in range(nj):
        for k in range(pn+1):
            m = j_[j][k]
            n = j__[j][k]
            p = j___[j][k]
            C[j][k] = 0.0
            if k == m:
                C[j][k] = dot(hn[p],hn[m])/(ln[m] * dot(hn[p], kn[m])) - dot(hn[n],hn[m])/(ln[m] * dot(hn[n], kn[m]))
            if k == n:
                C[j][k] = -1 * dot(hn[m],hn[m])/(ln[n] * dot(hn[m], kn[n]))
            if k == p:
                C[j][k] = dot(hn[m],hn[m])/(ln[p] * dot(hn[m], kn[p]))
            if k == pn:
                C[j][k] = -1 * ( dot(hn[p],hn[m])/(ln[m] * dot(hn[p], kn[m])) - dot(hn[n],hn[m])/(ln[m] * dot(hn[n], kn[m])) ) -1 * (-1 * dot(hn[m],hn[m])/(ln[n] * dot(hn[m], kn[n])) ) -1 * ( dot(hn[m],hn[m])/(ln[p] * dot(hn[m], kn[p])) )
    
    # print('Local Matrix C ext')
    # print(C.shape)
    # print(k_lg)
    # print(uv_lg)

    return C, k_lg, uv_lg

def assembly_Cf(form, plot = False):

    Cn = {}
    nodes_lg = {}
    edges_lg = {}

    k_i = form.key_index()
    uv_i = form.uv_index()

    for key in form.vertices():
        i = k_i[key]
        if key not in form.vertices_on_boundary():
            Cn[i], nodes_lg[i], edges_lg[i] = local_matrix(form, key, plot=plot)
        else:
            Cn[i], nodes_lg[i], edges_lg[i] = local_matrix_external(form, key, plot= plot)

    # Build Global Matrix Cf

    N = form.number_of_vertices()
    E = form.number_of_edges()
    ext_edges = []
    for u, v in form.edges_on_boundary():
        try:
            ext_edges.append(uv_i[(u,v)])
        except:
            ext_edges.append(uv_i[(v,u)])
    edges_int = E - len(form.edges_on_boundary())
    print('Form has {0} interior edges\n   {1} bound edges\n   {2} total nodes\n   {3} boundaries nodes'.format(edges_int,len(ext_edges),N,len(form.vertices_on_boundary())))
    Cf = zeros((E,N))
    if plot:
        print(Cf.shape)
    for i in range(N):
        Clocal = Cn[i]
        node_lg = nodes_lg[i]
        edge_lg = edges_lg[i]
        for j in range(Clocal.shape[0]):
            for k in range(Clocal.shape[1]):
                j_ = edge_lg[j]
                k_ = node_lg[k]
                Cf[j_][k_] += Clocal[j][k]

    for u,v in form.edges_on_boundary():
        try:
            i = uv_i[(u,v)]
        except:
            i = uv_i[(v,u)]

    return Cf

def A_heights(form):

    uv_i = form.uv_index()
    k_i = form.key_index()

    N = form.number_of_vertices()
    E = form.number_of_edges()
    A = zeros((N,E))

    for key in form.vertices():
        ngb = form.vertex_neighbors(key,ordered=True)
        zi = form.get_vertex_attribute(key,'z')
        i_vertex = k_i[key]
        for m in ngb:
            if m not in form.edges_on_boundary():
                zm = form.get_vertex_attribute(m,'z')
                try:
                    i_edge = uv_i[key,m]
                    h_ij = form.edge_length(key,m)
                except:
                    i_edge = uv_i[m,key]
                    h_ij = form.edge_length(m,key)
                val = (zi - zm)/h_ij
                A[i_vertex][i_edge] += val

    return A 

def A_stress(form, Rm):

    uv_i = form.uv_index()
    k_i = form.key_index()

    N = form.number_of_vertices()
    A = zeros((N,N))

    for key in form.vertices():
        ngb = form.vertex_neighbors(key,ordered=True)
        i_hor = k_i[key]
        for m in ngb:
            if m not in form.edges_on_boundary():
                i_ver = k_i[m]
                try:
                    i_edge = uv_i[key,m]
                    h_ij = form.edge_length(key,m)
                except:
                    i_edge = uv_i[m,key]
                    h_ij = form.edge_length(m,key)
                Rmij = Rm[i_edge]
                val = Rmij/h_ij
                A[i_hor][i_ver] += - 1 * val
                A[i_hor][i_hor] += val

    return A 

def hessian(form):

    # Method per Node
    
    for key in form.vertices():
        area = form.get_vertex_attribute(key, 'pz')
        neighbors = form.vertex_neighborhood(key)
        # jump = Array([[0,0],[0,0]])
        u = key
        for v in neighbors:
            edge = Array(form.vertex_coordinates(v)[:2] + [0]) - Array(form.vertex_coordinates(u)[:2] + [0])
            hi = cross(edge, [0,0,1])
            hi_ = normalize_vector(hi)
            Hi = tensorproduct(hi_,hi_)
            # print(Hi) # Check if it should be planar
            df = form.vertex_coordinates(v)[2] - form.vertex_coordinates(u)[2]
            jump += df * Hi
        form.set_vertex_attribute(key, 'jump', jump)
        form.set_vertex_attribute(key, 'hessian', jump/area)
        print(jump/area)

    # Method per edge connected to the node

    for key in form.vertices():
        area = form.get_vertex_attribute(key, 'pz')
        neighbors = form.vertex_neighborhood(key)
        hess = Array([[0,0,0],[0,0,0],[0,0,0]])
        u = key
        for v in neighbors:
            try:
                dfHi = form.get_edge_attribute((u,v), 'jump')
            except:
                dfHi = form.get_edge_attribute((v,u), 'jump')
            hess += dfHi
        form.set_vertex_attribute(key, 'hessian', hess)
        print(hess)

    return


def simple_nurbs(a,b,h, par=20, plot = False):

    from geomdl import CPGen
    from geomdl import BSpline
    from geomdl import NURBS
    from geomdl import utilities
    from geomdl.visualization import VisMPL
    from matplotlib import cm

    # Generate a plane with the dimensions 50x100
    surfgrid = CPGen.Grid(a, b)

    # Generate a grid of 25x30
    surfgrid.generate(2, 2)

    # Generate bumps on the grid
    # surfgrid.bumps(num_bumps=5, bump_height=20, base_extent=8)

    # Create a BSpline surface instance
    surf = BSpline.Surface()

    # Set degrees
    surf.degree_u = 2
    surf.degree_v = 2

    # Get the control points from the generated grid
    surf.ctrlpts2d = surfgrid.grid
    surf.ctrlpts2d[1][1][2] = h

    # Set knot vectors
    surf.knotvector_u = utilities.generate_knot_vector(surf.degree_u, surf.ctrlpts_size_u)
    surf.knotvector_v = utilities.generate_knot_vector(surf.degree_v, surf.ctrlpts_size_v)
    # print(surf.knotvector_u)

    # Set sample size
    surf.sample_size = par

    if plot:
        # Set visualization component
        surf.vis = VisMPL.VisSurface(ctrlpts=True, legend=False)

        # Plot the surface
        surf.render(colormap=cm.cool)

    return surf