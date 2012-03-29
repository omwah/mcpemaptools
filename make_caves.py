#!/usr/bin/env python

import os
import sys
import logging
from optparse import OptionParser

from numpy import round, mod
from math import degrees, radians, floor

from map_view import MapView
from caving import make_cave, tunnel_pattern
from utils import load_world_and_player, get_player_pos_yaw

def standalone_main():
    parser = OptionParser("[options] <world_filename>")
    parser.add_option("-v", "--verbose",
                      action="store_true", dest="verbose", default=False,
                      help="print debugging values")

    (options, args) = parser.parse_args()

    # Set up logging so we can see debug messages from pymclevel
    logger = logging.getLogger()
    sh=logging.StreamHandler()
    logger.addHandler(sh)
    if options.verbose:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    if len(args) < 1:
        parser.error("Must specify world file location or filename.")

    # Load world and player file (level.dat) from same place
    world, player = load_world_and_player(args[0])
    
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
    logger.info("Writing changes in place")
    world.saveInPlace()

    # Remove the logger handler so if we rerun in ipython
    # we dont start getting duplicate log messages
    logger.removeHandler(sh)

if __name__ == "__main__":
    standalone_main()
