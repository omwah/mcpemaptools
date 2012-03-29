import os
import logging

from math import radians, degrees
from numpy import array, mod

from pymclevel.pocket import PocketWorld
from opennbt import NBTFile

logger = logging.getLogger(__name__)

def load_world_and_player(w_file):
    # w_file can be either a path or filename
    # either way chunks.dat gets loaded
    world = PocketWorld(w_file)
    logger.info("Loaded world file: %s" % world.filename)

    # Fix incorrect bounding box sizes
    all_chunks = array(world.allChunks)
    maxx = (max(all_chunks[:,0])+1)*16
    maxz = (max(all_chunks[:,1])+1)*16
    world.Width = maxx
    world.Length = maxz

    # Load level file from same path as world file
    p_file = os.path.join(os.path.dirname(world.filename), "level.dat")
    player = NBTFile(p_file, compressed=False)
    logger.info("Loaded player file: %s" % p_file)

    return world, player

def get_player_pos_yaw(player):
    """Return player posistion rounded to nearest integer point and
    yaw value in radians"""

    # Extract player posistion from NBT file and convert to numpy array
    player_pos = array([ round(pval.value) for pval in player.value['Player'].value['Pos'].value ])
    logger.debug("Player posistion: %s" % player_pos)

    # Player yaw in radians, modulo 360
    player_yaw = radians(mod(player.value['Player'].value['Rotation'].value[0].value, 360))
    logger.debug("Player yaw: %s" % degrees(player_yaw))

    return player_pos, player_yaw
