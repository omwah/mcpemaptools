import logging
from numpy import array, where, mod, random, ravel
from math import degrees, radians

# Define a pattern in the x * y or z * y dimension which will
# replace existing blocks where caving is in progress. A value
# of -1 means keep existing blocks. The matrix is oriented so
# so first dimension is decreasing y and second is increasing 
# x or z so that it is easier to visualize what will be applied.
# 
# Patterns are odd in size so that rotation around center works
# nicely
tunnel_pattern = array([
        [[-1, -1, -1, -1, -1,],
         [-1,  0,  0,  0, -1,],
         [-1,  0,  0,  0, -1,],
         [ 0,  0,  0,  0,  0,],
         [ 48, 1,  1,  1, 48,],],

        [[-1, -1, -1, -1, -1,],
         [-1,  0,  0,  0, -1,],
         [ 0,  0,  0,  0,  0,],
         [ 0,  0,  0,  0,  0,],
         [ 1, 48,  1, 48,  1,],],

        [[-1, -1, -1, -1, -1,],
         [ 0,  0,  0,  0,  0,],
         [ 0,  0,  0,  0,  0,],
         [ 0,  0,  0,  0,  0,],
         [ 1,  1, 48,  1,  1,],],
        ])

logger = logging.getLogger(__name__)

def make_cave(view, pattern, 
              max_cave_len=250, 
              rotate_dir_prob=0.5, # Probability to prefer 90 over -90 deg
              do_rotate_prob=0.5, turns_till_rotate=10,
              shear_range=(-1, 1), vert_inc_prob=0.4,
              branch_prob=0.3, turns_till_branch=20, branch_level=0):

    # Mark which points we will actually set within the pattern
    where_set = where(pattern > -1)

    # How many blocks we move is based on how big the pattern
    # is in the z direction
    forward_inc = pattern.shape[0]
    
    cave_len = 0
    turns_since_rotate = 0
    turns_since_branch = 0
    keep_caving = True
    while cave_len < max_cave_len:
    
        if not view.in_bounds():
            logger.debug("Cave went out of bounds, quiting.")
            break
        elif all(ravel(view.map_data()) == 0):
            logger.debug("Hit air pocket\n%s" % view.map_data())
            break
        elif any(ravel(view.map_data()) == view.world.materials.Bedrock.ID):
            # Lets not go past any bedrock blocks or else we might
            # make a hole in the world
            logger.debug("Hit bedrock\n%s" % view.map_data())
            break

        # Get current map slice and apply pattern
        curr_slice = view.map_data()
        curr_slice[where_set] = pattern[where_set]
        curr_slice = view.map_data(curr_slice)
        logger.debug("B: %d P: %s @ %f deg" % (branch_level,
                                               view.origin_position(), 
                                               mod(degrees(view.yaw), 360)))
        logger.debug("%s" % curr_slice)

        # For use by branching or turning
        if (random.sample() > (1-rotate_dir_prob)):
            turn_dir =  90
        else:
            turn_dir = -90

        # Change orientation every so often
        if(random.sample() > (1-do_rotate_prob) and turns_since_rotate > turns_till_rotate):
            logger.debug("Changing orientation by %f deg at cave length %d" % (turn_dir, cave_len))
            view.rotate_y(radians(turn_dir))
            turns_since_rotate = 0

        elif random.sample() > (1-branch_prob) and turns_since_branch > turns_till_branch:
            logger.debug("Launching branch by %f deg at cave length %d" % (turn_dir, cave_len))
            branch_view = view.clone()
            branch_view.rotate_y(radians(turn_dir))
    
            # Recurse to make branch cave. 
            make_cave(branch_view, pattern, 
                      max_cave_len=max_cave_len/2, # Not the main tunnel so make it shorter
                      rotate_dir_prob=rotate_dir_prob,
                      do_rotate_prob=do_rotate_prob, 
                      turns_till_rotate=turns_till_rotate,
                      shear_range=shear_range, 
                      vert_inc_prob=vert_inc_prob,
                      branch_prob=0, # Set likelihood of a new branch from this one to 0.0
                      turns_till_branch=turns_till_branch, 
                      branch_level=branch_level+1)
            turns_since_branch = 0
        else:
            # Random amount of side to side and vertical motion, equally likely
            shear_inc = random.random_integers(*shear_range)

            # Random vertical motion
            # Pick among -1, 0, or 1
            y_inc = random.binomial(2, vert_inc_prob)-1 

            # Go forward relative to the current orientation,
            # Move forward the size of the number of patterns in the z axis
            view.translate_relative((shear_inc, y_inc, forward_inc))
            cave_len += forward_inc

            turns_since_rotate += 1
            turns_since_branch += 1
    
    # Mark that we hit the cave
    if cave_len > max_cave_len:
        logger.debug("Hit max cave length, %d" % max_cave_len)

    logger.debug("Cave was %d blocks long" % (cave_len))
