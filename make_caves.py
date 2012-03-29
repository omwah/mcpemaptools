#!/usr/bin/env python

import os
import sys
import logging

from numpy import round, mod
from math import degrees, radians, floor

from map_view import MapView
from caving import make_cave, tunnel_pattern
from utils import load_world_and_player, get_player_pos_yaw

# Set up logging so we can see debug messages from pymclevel
logger = logging.getLogger()
sh=logging.StreamHandler()
logger.addHandler(sh)
logger.setLevel(logging.DEBUG)

# Load world and player file (level.dat) from same place
world, player = load_world_and_player(sys.argv[1])

# Extract player posistion and yaw from NBT file
player_pos, player_yaw = get_player_pos_yaw(player)

# Get closest yaw to something divisible by 90 deg
player_yaw = radians(90*round(degrees(player_yaw)/90))

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
