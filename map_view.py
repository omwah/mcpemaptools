import logging

from math import sin, cos, radians, degrees
from numpy import array, zeros, dot, round, all

logger = logging.getLogger(__file__)

class MapView(object):
    """Creates a 3D view of a box of Minecraft blocks where the view
    is oriented with the dimensions of z * y * x * coords
    where coords is the 3d coordinates of the view's blocks.
    In a default orientation of 0 deg with a right handed coordinate
    system the values of y and x will be decreasing from the top left
    and z will be in increasing order."""

    def __init__(self, world, view_shape, pos=(0,0,0), yaw=0, **kwargs):
        self.world = world
        self.yaw = yaw

        if len(view_shape) != 3:
            raise Exception("view_shape must be 3 numbers z size, y size and x size")
        self.view = zeros(list(view_shape) + [4], dtype=int)
    
        self.pos = pos

        self.set_position(self.pos, **kwargs)
        self.rotate_y(yaw)

    def position(self):
        """Returns posistion from which the view originates,
        ie: The bottom right corner of the 0th z dimension"""

        return self.view[0, -1, -1, :3]

    def set_position(self, pos, increment=(1,1,1)):
        """Default increment values will give view matrix oriented as
        described in the class doc string"""
        
        x_beg, y_beg, z_beg = pos
        x_inc, y_inc, z_inc = increment

        z_size, y_size, x_size = self.view.shape[:3]

        z_world = z_beg
        for z_view in range(0, z_size):
            y_world = y_beg
            for y_view in range(y_size-1, -1, -1):
                x_world = x_beg
                for x_view in range(x_size-1, -1, -1):
                    self.view[z_view, y_view, x_view, :] = (x_world, y_world, z_world, 1)
                    x_world += x_inc
                y_world += y_inc
            z_world += z_inc

        return self.view

    def apply_transformation(self, Tmatrix):
        if len(Tmatrix.shape) != 2 and Tmatrix.shape != (4, 4):
            raise Exception("Tmatrix must be of shape (4, 4), not: %s" % Tmatrix.shape)
        
        for z_view in range(self.view.shape[0]):
            for y_view in range(self.view.shape[1]):
                for x_view in range(self.view.shape[2]):
                    self.view[z_view, y_view, x_view, :] = dot(Tmatrix, self.view[z_view, y_view, x_view, :])

        return self.view
            

    @classmethod
    def translation_matrix(cls, displacement):
        Tx, Ty, Tz = displacement
        T = array([[1, 0, 0, Tx],
                   [0, 1, 0, Ty],
                   [0, 0, 1, Tz],
                   [0, 0, 0,  1]])
        return T

    def translate_absolute(self, displacement):
        T = MapView.translation_matrix(displacement)
        return self.apply_transformation(T)

    def translate_relative(self, displacement):
        d_affine = array(displacement)
        d_affine.resize(4)
        d_affine[3] = 1
        Tr = MapView.rotation_matrix_y(-self.yaw)
        trans = dot(Tr, d_affine)
        return self.translate_absolute(trans[:3])

    @classmethod
    def rotation_matrix_y(cls, angle):
        T = array([[ cos(angle),    0, sin(angle), 0],
                   [         0,     1,          0, 0],
                   [-sin(angle),    0, cos(angle), 0],
                   [          0,    0,          0, 1]])
        return T

    def rotate_y(self, angle):
        # Keep track for current posistion
        self.yaw += angle
        
        orig_pos = self.position()

        # Translate back to origin, rotate, then translate back    
        Tt1 = MapView.translation_matrix(-orig_pos)
        Tr = MapView.rotation_matrix_y(angle)
        Tt2 = MapView.translation_matrix(orig_pos)

        return self.apply_transformation(dot(Tt2, dot(Tr, Tt1)))

    def map_data(self, set_val=None):
        if set_val != None and tuple(set_val.shape) != tuple(self.view.shape[:3]):
            raise Exception("set_val must have shape of %s to match view shape, not: %s" % (self.view.shape[:3], set_val.shape))

        out_data = zeros(self.view.shape[:3], dtype=int)

        for z_view in range(self.view.shape[0]):
            for y_view in range(self.view.shape[1]):
                for x_view in range(self.view.shape[2]):
                    world_pos = [ round(p) for p in self.view[z_view, y_view, x_view, :3] ]
                    if set_val != None:
                        new_v = set_val[z_view, y_view, x_view]
                        self.world.setBlockAt(world_pos[0], world_pos[1], world_pos[2], new_v)
                    out_data[z_view, y_view, x_view] = self.world.blockAt(*world_pos)

        return out_data

    def bounds_matrix(self):
        bb = self.world.getWorldBounds()
        
        view_in_bounds = zeros(self.view.shape[:3], dtype=bool)
        for z_view in range(self.view.shape[0]):
            for y_view in range(self.view.shape[1]):
                for x_view in range(self.view.shape[2]):
                    view_in_bounds[z_view, y_view, x_view] = \
                        bb.minx <= self.view[z_view, y_view, x_view, 0] < bb.maxx and \
                        bb.miny <= self.view[z_view, y_view, x_view, 1] < bb.maxy and \
                        bb.minz <= self.view[z_view, y_view, x_view, 2] < bb.maxz
        return view_in_bounds

    def in_bounds(self):
        return all(self.bounds_matrix())
                        
