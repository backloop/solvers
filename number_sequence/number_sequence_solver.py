#!/usr/bin/python3
import time
import sys
import signal
import multiprocessing
import queue
import os

#
# INITIAL SETUP
#

if not len(sys.argv[1:]) in (2,3):
    print("usage: %s nrows ncols [#processes]" % sys.argv[0])
    exit(1)

sy = int(sys.argv[1])
sx = int(sys.argv[2])

num_proc = os.cpu_count()
if len(sys.argv[1:]) == 3:
    num_proc = int(sys.argv[3])
print("Running %d processes in parallel" % num_proc)

#
# PRE-CALCULATE MOVEMENT TABLE
#

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
# PRE-CALCULATE MINIMAL SET OF START POSITIONS
#

if sx == sy:
    print("\nRotational symmetry of a square board reduces the search space")
    start_positions = []
    start = 0
    stop = sx-1
    while (start < stop):
        start_positions.extend(tuple(range(start, stop)))
        start += sx + 1;
        stop += sx - 1;
    if start == stop:
        start_positions.append(start)

    print("Search space of starting positions:")
    print(start_positions)
#    5x5 : start_positions = (0, 1, 2, 3, 6, 7, 12)
#    6x6 : start_positions = (0, 1, 2, 3, 4, 7, 8, 9, 14)
#    7x7 : start_positions = (0, 1, 2, 3, 4, 5, 8, 9, 10, 11, 16, 17, 24)
else:
    print("Symmetries uncalculated, optimizations might be possible")
    start_positions = range(sx*sy)

#
# MAIN ALGORITHM
#

num_solutions = 0
last_board = None
def recursive_move(stats_cb, queue, board, pos, num):
    global num_solutions

    stats_cb(queue, board)
    if num > (sx * sy):
        # solved
        num_solutions += 1
        global last_board
        last_board = board.copy()
    else:
        m = 0
        for cpos in moves[pos]:
            if board[cpos] == 0:
                m += 1
                board[cpos] = num
                recursive_move(stats_cb, queue, board, cpos, num + 1)
                board[cpos] = 0

#
# SIGNAL HANDLING
#

def signal_handler(sig, frame):
    # only main thread should output to console
    if multiprocessing.active_children():
        print("")
        print("")
        print("You pressed Ctrl+C! ")

        if not last_boards:
            print("No solutions found yet...")
        else:
            print("solutions so far: %d" % (sum(solutions.values()) * (sx*sy)/len(start_positions)))
            print("last solutions:")
            pretty_print(last_boards.values())
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
print("\nPress Ctrl+C to stop execution")

#
# PRETTY PRINTING HELPERS
#

# print the data structure as a matrix
def pretty_print(boards):
    precision = len(str(sx*sy))
    for y in range(sy):
        for board in boards:
            if board:
                for x in range(sx):
                    print("{:{prec}} ".format(board[(sx * y) + x], prec=precision), end="");
                print(" | ", end="")
        print("")

# make space for runtime visualization
def empty_print():
    print("")
    print("")
    print("")
    for n in range(sy):
        print("")


if num_proc == 1:
    #
    # SINGLE PROCESS EXECUTION
    #
    # GENERAL PERFORMANCE (on my machines)
    # Without multiprocessing (full debug prints):          10k moves/s
    # Without multiprocessing (1/s debug prints):           ~3M moves/s
    #

    #
    # COLLECT STATISTICS
    #
    start = time.process_time()
    i = 0
    # Only do runtime visualization prints every nth iteration. Increasing
    # frequency drastically decreases performance.
    # It is a deliberate decision to not calculate the
    # passing of a second, but instead only compare to "max" valu
    # (set through testing) to avoid calling time.preocess_time() too often...
    def collect_statistics_sequential(queue, board):
        global start
        global i

        # Throttle statistics collection as it affects performance
        max = 1000000
        i += 1

        if i == max:
            now = time.process_time()
            dt = now - start
            start = now
            i = 0

            print("\033[A", end="")
            print("\033[A", end="")
            print("\033[A", end="")
            for n in range(sy):
                print("\033[A", end="")

            print("rate: {:9.0f} moves/s".format(max / dt))
            print("solutions so far: %d" % (num_solutions * (sx*sy)/len(start_positions)))
            if False:
                print("snaphot of board:")
                pretty_print((board,))
            else:
                print("last solution:")
                pretty_print((last_board,))

    # single instance, global board (low memory footprint)
    board = [0,] * (sx * sy)

    empty_print()
    results = []
    for pos in start_positions:

        # calculate
        board[pos] = 1
        recursive_move(collect_statistics_sequential, None, board, pos, 2)
        results.append(num_solutions - sum(results))
        print(results)
        board[pos] = 0

    print(results)
    print("solutions: %d" % (num_solutions * (sx*sy)/len(start_positions)))
    print("last solution:")
    pretty_print((last_board,))

else:
    #
    # PARALLEL PROCESS EXECUTION
    #
    # GENERAL PERFORMANCE (on my machines)
    #
    # With multiprocessing (8 cores) (1/s debug prints): ~13M moves/s (but only 1.7M per core)
    #

    #
    # COLLECT STATISTICS
    #
    start = time.process_time()
    i = 0
    # Only do runtime visualization prints every nth iteration. Increasing
    # frequency drastically decreases performance.
    # It is a deliberate decision to not calculate the
    # passing of a second, but instead only compare to "max" valu
    # (set through testing) to avoid calling time.preocess_time() too often...
    def collect_statistics_parallel(queue, board):
        global start
        global i

        # Throttle statistics collection as it affects performance
        max = 300000
        i += 1

        if i == max:
            now = time.process_time()
            dt = now - start
            queue.put({ "pid": os.getpid(),
                        "rate": (max/dt),
                        "board": board,
                        "last_board": last_board,
                        "num_solutions": num_solutions})
            start = now
            i = 0

    #
    # TASK THAT CAN BE MADE IN PARALLEL
    #
    def task(pos, queue, stats_cb):
        global num_solutions
        # single instance, global board (low memory footprint)
        board = [0,] * (sx * sy)

        # keep track of running processes for statistics
        queue.put({"pid": os.getpid(), "running": True})

        # calculate
        num_solutions  = 0
        board[pos] = 1
        recursive_move(stats_cb, queue, board, pos, 2)

        # keep track of running processes for statistics
        queue.put({"pid": os.getpid(), "running": False})

        return (num_solutions, last_board)

    #
    # LOAD PARALLEL TASKS AND PROCESS EVENT QUEUE
    #

    stats_cb = collect_statistics_parallel
    manager = multiprocessing.Manager()
    # rename queue due to conflict with package "queue"
    _queue = manager.Queue()
    job_args = [(pos, _queue, stats_cb) for pos in start_positions]
    rates = {}
    boards = {}
    last_boards = {}
    solutions = {}

    with multiprocessing.Pool(num_proc) as pool:
        async_result = pool.starmap_async(task, job_args)

        pool.close()

        print("-" * 20)

        cnt = 0
        max = 0

        empty_print()
        while not async_result.ready():
            try:
                message = _queue.get(block=False)

                if "running" in message:
                    if message["running"]:
                        pass
                        continue
                    if not message["running"]:
                        # delete keys if they exist, return None as fallback
                        rates.pop(message["pid"], None)
                        boards.pop(message["pid"], None)
                        last_boards.pop(message["pid"], None)
                        solutions.pop(message["pid"], None)
                        continue

                if "rate" in message:
                    rates[message["pid"]] = message["rate"]
                    boards[message["pid"]] = message["board"]
                    last_boards[message["pid"]] = message["last_board"]
                    solutions[message["pid"]] = message["num_solutions"]

                    print("\033[A", end="")
                    print("\033[A", end="")
                    print("\033[A", end="")
                    for n in range(sy):
                        print("\033[A", end="")

                    values = rates.values()
                    print("rates ({:d}): total: {:9.0f} moves/s, per process: {:9.0f} moves/s".format(len(values), sum(values), sum(values)/len(values)))
                    values = solutions.values()
                    print("solutions so far: %d" % (sum(values) * (sx*sy)/len(start_positions)))
                    if False:
                        print("snaphot of boards:")
                        pretty_print(boards.values())
                    else:
                        print("last solutions:")
                        pretty_print(last_boards.values())

                    continue

            except queue.Empty:
                pass

    print("")
    results = [result[0] for result in async_result.get()]
    print(results)
    print("total solutions: %d" % (sum(results) * (sx*sy)/len(start_positions),))
    print("last solutions:")
    pretty_print([result[1] for result in async_result.get()])
