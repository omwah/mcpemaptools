#!/usr/bin/env python

import os
import sys
import logging
from optparse import OptionParser

from numpy import round, mod, random
from math import degrees, radians, floor

from map_view import MapView
from utils import load_world_and_player, get_player_pos_yaw
from caving import *

def player_tunnel(world, player, **kwargs):
    """Make a tunnel starting at player locating in the same visual direction"""

    # Extract player posistion and yaw from NBT file
    player_pos, player_yaw = get_player_pos_yaw(player)

    # Get closest yaw to something divisible by 90 deg
    player_yaw = radians(90*round(degrees(player_yaw)/90))

    # Set up view object we will use to move through the world
    cave_view = MapView(world, tunnel_pattern.shape, player_pos, yaw=player_yaw)

    # Move starting point centered in front of player, 
    # a bit in front and a bit down
    cave_view.translate_relative((floor(tunnel_pattern.shape[2]/2.0), -floor(tunnel_pattern.shape[1]/2.0), tunnel_pattern.shape[0]))

    make_cave(cave_view, tunnel_pattern, **kwargs)
    
def random_subsurface(world, pattern, **kwargs):
    """Creates a sub surface tunnel starting at a random location"""

    bb = world.getWorldBounds()
    x_start = random.randint(bb.minx, bb.maxx)
    z_start = random.randint(bb.minz, bb.maxz)
    y_start = find_ground_level(world, (x_start, z_start))

    start_pos = (x_start, y_start, z_start)
    start_yaw = radians(random.randint(0, 4) * 90)
    logger.info("Beginning random subsurface tunnel at: %s %f deg" % (start_pos, degrees(start_yaw)))

    cave_view = MapView(world, pattern.shape, start_pos, yaw=start_yaw)

    make_cave(cave_view, pattern, **kwargs)

def standalone_main():
    parser = OptionParser("[options] <world_filename>")

    parser.add_option("-p", "--player_tunnel",
                      action="store_true", dest="player_tunnel", default=False,
                      help="Make a tunnel starting at player position")

    parser.add_option("-r", "--num_random_tunnels",
                      type="int",
                      dest="num_random_tunnels", default=0,
                      help="Number of random sub surface tunnels to make")

    parser.add_option("-l", "--num_lava_tubes",
                      type="int",
                      dest="num_lava_tubes", default=0,
                      help="Number of lava tubes to make")

    parser.add_option("-w", "--num_water_tubes",
                      type="int",
                      dest="num_water_tubes", default=0,
                      help="Number of water tubes to make")

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
    
    if options.player_tunnel:
        logger.info("Constructing tunnel at player location")
        player_tunnel(world, player)

    for count in range(options.num_random_tunnels):
        logger.info("Creating random subsurface tunnel #%d" % (count+1))
        random_subsurface(world, tunnel_pattern)

    for count in range(options.num_lava_tubes):
        logger.info("Creating random subsurface lava tubes #%d" % (count+1))
        random_subsurface(world, lava_tube)

    for count in range(options.num_water_tubes):
        logger.info("Creating random subsurface water tubes #%d" % (count+1))
        random_subsurface(world, water_tube)

    # Generate lights for dirty chunks
    logger.info("Generating lights")
    world.generateLights()

    # Save our changes
    logger.info("Writing changes in place")
    world.saveInPlace()

    # Remove the logger handler so if we rerun in ipython
    # we dont start getting duplicate log messages
    logger.removeHandler(sh)

if __name__ == "__main__":
    standalone_main()
