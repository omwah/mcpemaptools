#!/usr/bin/env python

import os
import sys
import logging
import random

from numpy import array, zeros, round, where, mod, ravel, dot, random
from math import degrees, radians

from pymclevel.pocket import PocketWorld
from opennbt import NBTFile

from map_view import MapView

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
cave_pattern = array([
        [[-1, -1, -1, -1, -1,],
         [-1, -1, -1, -1, -1,],
         [-1,  0,  0,  0, -1,],
         [-1,  0,  0,  0, -1,],
         [ 1,  0,  0,  0,  1,],
         [ 1,  1,  1,  1,  1,],],

        [[-1, -1, -1, -1, -1,],
         [-1, -1, -1, -1, -1,],
         [-1,  0,  0,  0, -1,],
         [-1,  0,  0,  0, -1,],
         [ 1,  0,  0,  0,  1,],
         [ 1,  1,  1,  1,  1,],],
        ])

# Set up logging so we can see debug messages from pymclevel
logger = logging.getLogger()
sh=logging.StreamHandler()
logger.addHandler(sh)
logger.setLevel(logging.DEBUG)

w_file = sys.argv[1]
logger.info("Loading world file: %s" % w_file)
world = PocketWorld(w_file)

p_file = os.path.join(os.path.dirname(world.filename), "level.dat")
logger.info("Loading player file: %s" % p_file)
player = NBTFile(p_file, compressed=False)

# Extract player posistion from NBT file and convert to numpy array
player_pos = array([ round(pval.value) for pval in player.value['Player'].value['Pos'].value ])
logger.debug("Player posistion: %s" % player_pos)

# Get closest yaw to something divisible by 90 deg
player_yaw = mod(player.value['Player'].value['Rotation'].value[0].value, 360)
player_yaw = radians(90*round(player_yaw/90))
logger.debug("Player yaw: %s" % degrees(player_yaw))

# Set up view object we will use to move through the world
cave_view = MapView(world, cave_pattern.shape, player_pos, yaw=player_yaw)

# Move starting point centered in front of player, 
# a bit in front and a bit down
cave_view.translate_relative((cave_pattern.shape[2]/2, -cave_pattern.shape[1]/2, cave_pattern.shape[0]))

# Mark which points we will actually set with the pattern
where_set = where(cave_pattern > -1)

count = 0
max_cave_len = 500
keep_caving = True
forward_inc = cave_pattern.shape[0]
while keep_caving:
    count += 1

    # Get current map slice and apply pattern
    curr_slice = cave_view.map_data()
    curr_slice[where_set] = cave_pattern[where_set]
    curr_slice = cave_view.map_data(curr_slice)
    logger.debug("%s @ %f deg" % (cave_view.position(), mod(degrees(cave_view.yaw), 360)))
    logger.debug("%s" % curr_slice)

    # Change orientation every so often
    if(random.uniform(0,1) > 0.5 and mod(count, 10) == 0):
        if (random.uniform(0,1) > 0.5):
            turn_dir =  90
        else:
            turn_dir = -90
        cave_view.rotate_y(radians(turn_dir))
        logger.debug("Changing orientation by %f at count %d" % (turn_dir, count))
    else:
        # Don't rotate and translate in same step, might create walls that make
        # cave seemingly dead end

        # Random amount of side to side and vertical motion, equally likely
        shear_inc = random.random_integers(-1, 1)

        # Random vertical motion
        # Pick among -1, 0, or 1 with -1 and 0 being more likely
        y_inc = random.binomial(2,0.4)-1 

        # Go forward relative to the current orientation,
        # Move forward the size of the number of patterns in the z axis
        cave_view.translate_relative((shear_inc, y_inc, forward_inc))

    if not cave_view.in_bounds():
        logger.debug("Cave went out of bounds, quiting.")
        keep_caving = False
    elif count*forward_inc > max_cave_len:
        logger.debug("Hit max cave length, %d" % max_cave_len)
        keep_caving = False
    elif all(ravel(cave_view.map_data()) == 0):
        logger.debug("Hit air pocket\n%s" % cave_view.map_data())
        keep_caving = False
    elif any(ravel(cave_view.map_data()) == world.materials.Bedrock.ID):
        # Lets not go past any bedrock blocks or else we might
        # make a hole in the world
        logger.debug("Hit bedrock\n%s" % cave_view.map_data())
        keep_caving = False

# Save our changes
world.saveInPlace()

logger.debug("Cave was %d blocks long" % (count * forward_inc))

# Remove the logger handler so if we rerun in ipython
# we dont start getting duplicate log messages
logger.removeHandler(sh)
