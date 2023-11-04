#!/usr/bin/python3
import time
import sys
import signal

#
# INITIAL SETUP
#

if len(sys.argv[1:]) != 2:
    print("usage: %s nrows ncols" % sys.argv[0])
    exit(1)

sy = int(sys.argv[1])
sx = int(sys.argv[2])

print("Table of the allowed moves as a function of current position")
moves = []
for y in range(sy):
    for x in range(sx):
        m = []
        pos = (y * sx) + x
        # up
        if (y - 3) >= 0:
            m.append(pos - 3*sx)
        # right
        if (x + 3) < sx:
            m.append(pos + 3)
        # down
        if (y + 3) < sy:
            m.append(pos + 3*sx)
        # left
        if (x - 3) >= 0:
            m.append(pos - 3)
        # up-right
        if (y - 2) >= 0 and (x + 2) < sx:
            m.append(pos - 2*sx + 2)
        # down-right
        if (y + 2) < sy and (x + 2) < sx:
            m.append(pos + 2*sx + 2)
        # down-left
        if (y + 2) < sy and (x - 2) >= 0:
            m.append(pos + 2*sx - 2)
        # up-left
        if (y - 2) >= 0 and (x - 2) >= 0:
            m.append(pos - 2*sx - 2)
        moves.append(m)
print(moves)

#
# PRETTY PRINTING HELPERS
#

# print the data structure as a matrix
def pretty_print(board):
    precision = len(str(sx*sy))
    for y in range(sy):
        for x in range(sx):
            print("{:{prec}} ".format(board[(sx * y) + x], prec=precision), end="");
        print("")

# print some stats during execution
start = time.process_time()
i = 0
def runtime_print(board):
    global start
    global i

    i += 1
    # Only print things every nth iteration. Increasing frequency here
    # drastically decreases performance. On my machine printing on each
    # move results in 10k moves/s. Printing approx once a second results
    # in 3M moves/s. It is a deliberate decision to not calculate the
    # passing of a second, but instead only compare to "max" value (set
    # through testing)
    max = 1000000
    if i == max:
        # clear board
        for n in range(sy):
            print("\033[A", end="")

        now = time.process_time()
        dt = now - start
        print("\033[A", end="")
        print("\033[A", end="")
        print("\033[A", end="")
        # add some spaces to clear of chars from previous prints
        print("total moves:   %.2e  " % num_moves)
        print("rate:          %.2e moves/s  " % (max/dt))
        print("solutions so far: %d" % (num_sol * (sx*sy)/len(starts)))
        start = now
        i = 0

        # print board
        pretty_print(board)
    #input("any key...")

def empty_print():
    for n in range(sy+3):
        print("")

#
# MAIN ALGORITHM
#

num_moves = 0
num_sol = 0
# avoid unnecessary multiplications. manual optimization. beware.
# seems to increase performance by ~.3% only...
board_size = sx * sy
last_board = None
def recursive_move(board, pos, num):
    global num_sol
    # tracking number of moves reduces performance
    # by 2.64e6/3.2e6 = 0.825 ~= 18%
    #global num_moves
    #num_moves += 1

    runtime_print(board)
    if num > board_size:
        # solved
        num_sol += 1
#        print("solution: ", num_sol)
#        pretty_print(board)
#        print("---"*sx)
        global last_board
        last_board = board.copy()
    else:
        m = 0
        for cpos in moves[pos]:
            if board[cpos] == 0:
                m += 1
                board[cpos] = num
                recursive_move(board, cpos, num + 1)
                board[cpos] = 0

# Calculate start positions
if sx == sy:
    print("\nRotational symmetry of a square board reduces the search space")
    starts = []
    start = 0
    stop = sx-1
    while (start < stop):
        starts.extend(tuple(range(start, stop)))
        start += sx + 1;
        stop += sx - 1;
    if start == stop:
        starts.append(start)

    print("Search space of starting positions:")
    print(starts)
#    5x5 : starts = (0, 1, 2, 3, 6, 7, 12)
#    6x6 : starts = (0, 1, 2, 3, 4, 7, 8, 9, 14)
#    7x7 : starts = (0, 1, 2, 3, 4, 5, 8, 9, 10, 11, 16, 17, 24)
else:
    print("Symmetries uncalculated, optimizations might be possible")
    starts = range(sx*sy)

# catch ctrl+c for unpatient users ;)
def signal_handler(sig, frame):
    print("")
    print("")
    print("You pressed Ctrl+C!")
    if not last_board:
        print("No solutions found yet...")
    else:
        print("solutions so far: %d" % (num_sol * (sx*sy)/len(starts)))
        print("last solution:")
        pretty_print(last_board)
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
print("\nPress Ctrl+C to stop execution")

# single instance, global board (low memory footprint)
board = [0,] * (sx * sy)

# loop over start positions
empty_print()
for pos in starts:
    board[pos] = 1
    recursive_move(board, pos, 2)
    board[pos] = 0

print("")
print("total moves: n/a")
#print("total moves: %d" % num_moves)
if not last_board:
    print("No solutions found...")
else:
    print("solutions: %d" % (num_sol * (sx*sy)/len(starts)))
    print("last solution:")
    pretty_print(last_board)

