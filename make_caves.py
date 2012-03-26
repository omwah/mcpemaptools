#!/usr/bin/env python

import os
import sys
import logging
import random

import numpy

from pymclevel.pocket import PocketWorld
from opennbt import NBTFile

# Define a "slice" in the x * y or z * y dimension which will
# replace existing blocks where caving is in progress. A value
# of -1 means keep existing blocks. The matrix is oriented so
# so first dimension is decreasing y and second is increasing 
# x or z so that it is easier to visualize what will be applied.
# 
# Make sure there is some empty space on the side of the mask
# or else when the cave changes dimension you will end up with
# a dead end. But this could be desired to make exploring the
# cave a bit more involved.
cave_mask = numpy.array([-1,  0,  0,  0, -1, 
                         -1,  0,  0,  0, -1,
                          0,  0,  0,  0,  0,
                          0,  0,  0,  0,  0,
                         -1, -1,  1, -1, -1,
                         -1,  9,  9,  9, -1]).reshape(6, 5)

# Set up logging so we can see debug messages from pymclevel
logger = logging.getLogger()
sh=logging.StreamHandler()
logger.addHandler(sh)
logger.setLevel(logging.DEBUG)

def map_slice(world, pos, size, set_val=None, swap_xz=False):
    """Returns or sets an array of block IDs into the world with the first 
dimension being decreasing y and the second increasing x or z. By default
the z dimension is iterated over unless swap_xz is true."""
    x_beg, y_beg, z_beg = pos
    y_size, lat_size = size

    if set_val != None and (len(set_val.shape) != 2 or set_val.shape[1] != lat_size or set_val.shape[0] != y_size):
        raise Exception("set_val of shape: %s which does not match x,y set size: %d, %d" % (set_val.shape, lat_size, y_size))

    out_data = numpy.zeros((y_size, lat_size), dtype=int)
    if swap_xz:
        lat_in = z_beg
    else:
        lat_in = x_beg

    for lat_out in range(lat_size):
        y_in = y_beg
        for y_out in range(y_size):
            if set_val != None:
                if swap_xz:
                    world.setBlockAt(x_beg, y_in, lat_in, set_val[y_size-y_out-1, lat_out])
                else:
                    world.setBlockAt(lat_in, y_in, z_beg, set_val[y_size-y_out-1, lat_out])
            if swap_xz:
                out_data[y_size-y_out-1, lat_out] = world.blockAt(x_beg, y_in, lat_in)
            else:
                out_data[y_size-y_out-1, lat_out] = world.blockAt(lat_in, y_in, z_beg)
            y_in += 1
        lat_in += 1
    return out_data

w_file = sys.argv[1]
logger.info("Loading world file: %s" % w_file)
world = PocketWorld(w_file)

p_file = os.path.join(os.path.dirname(world.filename), "level.dat")
logger.info("Loading player file: %s" % p_file)
player = NBTFile(p_file, compressed=False)

# Extract player posistion from NBT file and convert to numpy array
player_pos = [ int(pval.value) for pval in player.value['Player'].value['Pos'].value ]
logger.debug("Player posistion: %s" % player_pos)

# Make a pilar a bit away to make where cave begins
pilar = numpy.zeros((10, 1), dtype=int)
pilar[:,:] = world.materials.Obsidian.ID
map_slice(world, player_pos + numpy.array([0,-1,-2]), pilar.shape, pilar)

# Start a bit below where player stands, but leave a bit above surface so 
# we can find cave entrance
start_pos = numpy.array(player_pos) + numpy.array([0, -cave_mask.shape[0]+2, 0])

where_set = numpy.where(cave_mask > -1)
curr_pos = start_pos
swap_xz = False # Are we using x or z for slicing
swap_len = 0 # How far weve gone since changing from z or x direction
forward_inc = 1 # Either increment or decrement in the current forward directionx
while 0 < curr_pos[0] < 512 and 0 < curr_pos[1] < 512 and \
        cave_mask.shape[0] < curr_pos[1] < 128: # Don't completely hit bedrock
    # Get current map slice and apply mask
    curr_slice = map_slice(world, curr_pos, cave_mask.shape, swap_xz=swap_xz)
    curr_slice[where_set] = cave_mask[where_set]
    curr_slice = map_slice(world, curr_pos, cave_mask.shape[::-1], curr_slice, swap_xz=swap_xz)
    logger.debug("%s" % curr_slice)

    # Increment posistion according to which dimension we are currently moving
    lat_inc = numpy.round(random.uniform(-0.6,0.6))
    if swap_xz:
        curr_pos[0] += forward_inc
        curr_pos[2] += lat_inc
    else:
        curr_pos[0] += lat_inc
        curr_pos[2] += forward_inc
        
    # Possibly go down a bit
    curr_pos[1] += numpy.round(random.uniform(-0.6,0))

    # Swap x and z every so often
    if(random.uniform(0,1) > 0.6 and swap_len > 10):
        logger.debug("Changing x/z forward dimension!")
        swap_xz = not swap_xz
        swap_len = 0
        # Change direction in the dimension we are moving
        # very rarely
        if (random.uniform(0,1) > 0.9):
            logger.debug("Changing forward increment!")
            forward_inc *= -1
    else:
        swap_len += 1

# Remove the logger handler so if we rerun in ipython
# we dont start getting duplicate log messages
logger.removeHandler(sh)
