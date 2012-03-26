from pymclevel.pocket import PocketWorld
from opennbt import NBTFile

import os

import numpy
import logging
import random

cave_mask = numpy.array([-1,  0,  0,  0, -1, 
                         -1,  0,  0,  0, -1,
                          0,  0,  0,  0,  0,
                          0,  0,  0,  0,  0,
                         -1, -1,  1, -1, -1,
                         -1,  9,  9,  9, -1]).reshape(6, 5)

logger = logging.getLogger()
sh=logging.StreamHandler()
logger.addHandler(sh)
logger.setLevel(logging.DEBUG)

def z_slice(world, pos, size, set_val=None, swap_xz=False):
    x_beg, y_beg, z_beg = pos
    lat_size, y_size = size

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

print "Loading level..."
world = PocketWorld("../touchpad/games/com.mojang/minecraftWorlds/A Better One/")
p_file = os.path.join(os.path.dirname(world.filename), "level.dat")
player = NBTFile(p_file, compressed=False)

player_pos = [ int(pval.value) for pval in player.value['Player'].value['Pos'].value ]

# Make a pilar
pilar = numpy.zeros((10, 1), dtype=int)
pilar[:,:] = world.materials.Obsidian.ID
z_slice(world, player_pos + numpy.array([0,-1,-2]), pilar.shape[::-1], pilar)

start_pos = numpy.array(player_pos) + numpy.array([0, -5, 0])

swap_xz = False
where_set = numpy.where(cave_mask > -1)
curr_pos = start_pos
swap_len = 0
forward_inc = 1
while curr_pos[1] >= cave_mask.shape[0] and curr_pos[0] < 512 and curr_pos[1] < 512:
    map_slice = z_slice(world, curr_pos, cave_mask.shape[::-1], swap_xz=swap_xz)
    map_slice[where_set] = cave_mask[where_set]
    print map_slice
    print z_slice(world, curr_pos, cave_mask.shape[::-1], map_slice, swap_xz=swap_xz)
    if swap_xz:
        curr_pos[0] += forward_inc
        curr_pos[2] += numpy.round(random.uniform(-0.6,0.6))
    else:
        curr_pos[0] += numpy.round(random.uniform(-0.6,0.6))
        curr_pos[2] += forward_inc

    curr_pos[1] += numpy.round(random.uniform(-0.6,0))

    if(random.uniform(0,1) > 0.6 and swap_len > 10):
        swap_xz = not swap_xz
        swap_len = 0
        if (random.uniform(0,1) > 0.9):
            forward_inc *= -1
    else:
        swap_len += 1

logger.removeHandler(sh)
