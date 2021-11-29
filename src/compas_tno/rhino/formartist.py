from __future__ import print_function
from __future__ import absolute_import
from __future__ import division

import compas_rhino

from functools import partial
from math import sqrt
from math import pi
from compas_tno.rhino.diagramartist import DiagramArtist
from compas.utilities import color_to_colordict
from compas.geometry import add_vectors
from compas.geometry import scale_vector
from compas.geometry import length_vector
from compas.geometry import norm_vector

colordict = partial(color_to_colordict, colorformat='rgb', normalize=False)


__all__ = ['FormArtist']


class FormArtist(DiagramArtist):
    """Artist for form diagram in AGS.

    Parameters
    ----------
    form: compas_tno.diagrams.FormDiagram
        The form diagram to draw.

    Attributes
    ----------
    color_compression : 3-tuple
        Default color for compression.
    color_tension : 3-tuple
        Default color for tension.
    scale_forces : float
        Scale factor for the force pipes.
    tol_forces : float
        Tolerance for force magnitudes.
    """

    def __init__(self, form, layer=None):
        super(FormArtist, self).__init__(form, layer=layer)
        self.color_compression = (255, 0, 0)
        self.color_tension = (0, 255, 0)
        self.color_mesh_thrust = (0, 0, 0)
        self.color_mesh_intrados = (0, 0, 0)
        self.color_mesh_extrados = (0, 0, 0)
        self.color_mesh_middle = (0, 0, 0)
        self.color_vertex_extrados = (0, 255, 0)
        self.color_vertex_intrados = (0, 0, 255)
        self.color_faces = (0, 0, 0)
        self.scale_forces = 0.001
        self.pipes_scale = 0.01
        self.tol_forces = 0.001
        self.radius_sphere = 0.15
        self.layer = 'FormDiagram'

    # def draw_edges(self, edges=None, color=None, displacement=None, layer='Thrust'):
    #     """Draw a selection of edges.

    #     Parameters
    #     ----------
    #     edges : list, optional
    #         A selection of edges to draw.
    #         The default is ``None``, in which case all edges are drawn.
    #     color : tuple or dict of tuple, optional
    #         The color specififcation for the edges.
    #         The default color is black, ``(0, 0, 0)``.

    #     Returns
    #     -------
    #     list
    #         The GUIDs of the created Rhino objects.

    #     """
    #     edges = edges or list(self.diagram.edges_where({'_is_edge': True}))
    #     vertex_xyz = self.vertex_xyz
    #     if displacement:
    #         for key in vertex_xyz:
    #             vertex_xyz[key][0] += displacement[0]
    #             vertex_xyz[key][1] += displacement[1]
    #     edge_color = colordict(color, edges, default=self.color_edges)
    #     lines = []
    #     for edge in edges:
    #         lines.append({
    #             'start': vertex_xyz[edge[0]],
    #             'end': vertex_xyz[edge[1]],
    #             'color': edge_color[edge],
    #             'name': "{}.edge.{}-{}".format(self.diagram.name, *edge)})
    #     return compas_rhino.draw_lines(lines, layer=layer, clear=False, redraw=False)

    def redraw(self):

        compas_rhino.rs.EnableRedraw(True)

        return

    def draw_thrust(self, displacement=None):
        """Draw a mesh for the thrust network.

        Parameters
        ----------
        edges : list, optional
            A selection of edges to draw.
            The default is ``None``, in which case all edges are drawn.
        displacement : list, optional
            A displacement to add mesh to the scene.

        Returns
        -------
        list
            The GUIDs of the created Rhino object.

        """
        vertices, faces = self.diagram.to_vertices_and_faces()
        return compas_rhino.draw_mesh(vertices, faces, name="Thrust", color=self.color_mesh_thrust, disjoint=True, layer="Thrust-Mesh")

    def draw_cracks(self, color_intrados=(0, 0, 200), color_extrados=(0, 200, 0), layer=None, tol=10e-5):
        """Draw the intersection of the thrust network with intrados and extrados.

        Parameters
        ----------
        vertices : list, optional
            A selection of vertices to draw.
            The default is ``None``, in which case all vertices are drawn.
        displacement : list, optional
            A displacement to add mesh to the scene.
        tol : float, optional
            Acceptable error to find an intersection.

        Returns
        -------
        tuple with 2 lists
            List of the GUIDs of the created Rhino object, and the keys associated to it in the form diagram.

        """
        layer = layer or self.layer
        form = self.diagram
        intra_vertices = []
        extra_vertices = []
        intra_keys = []
        extra_keys = []
        for key in form.vertices():
            x, y, z = form.vertex_coordinates(key)
            lb = form.vertex_attribute(key, 'lb')
            ub = form.vertex_attribute(key, 'ub')
            if lb:
                if abs(z - lb) < tol:
                    intra_keys.append(key)
                    intra_vertices.append({
                        'pos': [x, y, z],
                        'name': "{}.vertex.{}".format("Intrados", key),
                        'color': self.color_vertex_intrados})
            if ub:
                if abs(z - ub) < tol:
                    extra_keys.append(key)
                    extra_vertices.append({
                        'pos': [x, y, z],
                        'name': "{}.vertex.{}".format("Extrados", key),
                        'color': self.color_vertex_extrados})

        guids_intra = compas_rhino.draw_points(intra_vertices, layer=layer + 'Intrados', color=color_intrados, clear=False, redraw=False)
        guids_extra = compas_rhino.draw_points(extra_vertices, layer=layer + 'Extrados', color=color_extrados, clear=False, redraw=False)
        return (guids_intra + guids_extra, intra_keys + extra_keys)

    # update this function
    def draw_from_attributes(self, attribute='target', name='mesh', displacement=None, color=None, join_faces=True, layer=None):
        """Draw a copy mesh of the form diagram whose height is defined based on the a given attribure.

        Parameters
        ----------
        attribute : str
            Attribute to base the heights of the network on.
        scale : float, optional
            The scaling factor for the load force vectors.
            The default value is ``0.01``
        layer : str, optional
            The layer to draw the output.

        Returns
        -------
        list
            A list with the guid of the corresponding load force vectors in Rhino.

        Notes
        -----
        The magnitude of the externally applied load at a vetex the attribute  `pz`.

        """

        faces = list(self.diagram.faces())
        layer = layer or self.layer
        vertex_xyz = self.vertex_xyz
        for key in vertex_xyz:
            z = self.diagram.vertex_attribute(key, attribute)  # Check my forms and remove this
            if type(z) == list:
                z = z[0]
            vertex_xyz[key][2] = z
            if displacement:
                vertex_xyz[key][0] += displacement[0]
                vertex_xyz[key][1] += displacement[1]
        face_color = colordict(color, faces, default=self.color_faces)
        facets = []
        for face in faces:
            facets.append({
                'points': [vertex_xyz[vertex] for vertex in self.diagram.face_vertices(face)],
                'name': "{}.face.{}".format(name, face),
                'color': face_color[face]})
        guids = compas_rhino.draw_faces(facets, layer=layer, clear=False, redraw=False)
        if not join_faces:
            return guids
        guid = compas_rhino.rs.JoinMeshes(guids, delete_input=True)
        compas_rhino.rs.ObjectLayer(guid, layer)
        compas_rhino.rs.ObjectName(guid, '{}'.format(name))
        if color:
            compas_rhino.rs.ObjectColor(guid, color)
        return

    def draw_loads(self, color=(255, 0, 0), scale=0.01, layer=None, tol=1e-3):
        """Draw the externally applied loads at all vertices of the diagram.

        Parameters
        ----------
        color : list or tuple, optional
            The RGB color specification for load forces.
            The specification must be in integer format, with each component between 0 and 255.
        scale : float, optional
            The scaling factor for the load force vectors.
            The default value is ``0.01``
        layer : str, optional
            The layer to draw the output.

        Returns
        -------
        list
            A list with the guid of the corresponding load force vectors in Rhino.

        Notes
        -----
        The magnitude of the externally applied load at a vetex the attribute  `pz`.

        """
        vertex_xyz = self.vertex_xyz
        lines = []

        for vertex in self.diagram.vertices():
            a = vertex_xyz[vertex]
            pz = -1 * self.diagram.vertex_attribute(vertex, 'pz')
            load = scale_vector((0, 0, 1), scale * pz)
            b = add_vectors(a, load)
            lines.append({'start': a, 'end': b, 'color': color, 'arrow': "start"})

        return compas_rhino.draw_lines(lines, layer=self.layer, clear=False, redraw=False)

    def draw_reactions(self, color=(255, 0, 0), scale=0.1, draw_as_pipes=False, layer=None, tol=1e-3):
        """Draw the reaction forces.

        Parameters
        ----------
        color : list or tuple
            The RGB color specification for load forces.
            The specification must be in integer format, with each component between 0 and 255.
        scale : float, optional
            The scaling factor for the load force vectors.
            The default value is ``0.01``
        layer : str, optional
            The layer to draw the output.

        Returns
        -------
        list
            A list with the guid of the corresponding load force vectors in Rhino.

        Notes
        -----
        The magnitude of the externally applied load at a vetex the attribute  `pz`.

        """
        layer = layer or self.layer
        vertex_xyz = self.vertex_xyz
        lines = []
        cylinders = []
        for key in self.diagram.vertices_where({'is_fixed': True}):
            a = vertex_xyz[key]
            r = self.diagram.vertex_attributes(key, ['_rx', '_ry', '_rz'])
            if not any(r):  # If receives null vector or None
                continue
            r = scale_vector(r, -1 * scale)
            if length_vector(r) < tol:
                continue

            b = add_vectors(a, r)
            lines.append({'start': a, 'end': b, 'color': color, 'arrow': "start"})
            if draw_as_pipes:
                force = self.pipes_scale * norm_vector(self.diagram.vertex_attributes(key, ['_rx', '_ry', '_rz']))
                print(force)
                cylinders.append({
                    'start': a,
                    'end': b,
                    'radius': sqrt(abs(force)/pi),
                    'color': color
                })

        if draw_as_pipes:
            print('ha')
            return compas_rhino.draw_cylinders(cylinders, self.layer, clear=False, redraw=False)
        else:
            return compas_rhino.draw_lines(lines, layer=self.layer, clear=False, redraw=False)

    def draw_forcepipes(self, color_compression=(255, 0, 0), color_tension=(0, 0, 255), tol=1e-3, layer=None):
        """Draw the forces in the internal edges as pipes with color and thickness matching the force value.

        Parameters
        ----------
        color_compression
        color_tension
        scale
        tol

        Returns
        -------
        list
            The GUIDs of the created Rhino objects.
        """
        layer = layer or self.layer
        vertex_xyz = self.vertex_xyz
        scale = self.pipes_scale
        cylinders = []
        for edge in self.diagram.edges_where({'_is_edge': True}):
            u, v = edge
            start = vertex_xyz[u]
            end = vertex_xyz[v]
            length = self.diagram.edge_length(*edge)
            q = self.diagram.edge_attribute(edge, 'q')
            force = q * length
            force = scale * force
            if abs(force) < tol:
                continue
            radius = sqrt(abs(force)/pi)
            pipe_color = color_compression if force < 0 else color_tension
            cylinders.append({
                'start': start,
                'end': end,
                'radius': radius,
                'color': pipe_color
            })
        return compas_rhino.draw_cylinders(cylinders, layer=layer, clear=False, redraw=False)
