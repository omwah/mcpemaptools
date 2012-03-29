#!/usr/bin/env python

import os
import sys
import logging
import random

from numpy import array, round, mod
from math import degrees, radians, floor

from pymclevel.pocket import PocketWorld
from opennbt import NBTFile

from map_view import MapView
from caving import make_cave, tunnel_pattern

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
cave_view = MapView(world, tunnel_pattern.shape, player_pos, yaw=player_yaw)

# Move starting point centered in front of player, 
# a bit in front and a bit down
cave_view.translate_relative((floor(tunnel_pattern.shape[2]/2.0), -floor(tunnel_pattern.shape[1]/2.0), tunnel_pattern.shape[0]))

make_cave(cave_view, tunnel_pattern)

# Save our changes
world.saveInPlace()

# Remove the logger handler so if we rerun in ipython
# we dont start getting duplicate log messages
logger.removeHandler(sh)
