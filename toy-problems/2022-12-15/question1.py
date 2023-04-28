"""

Inputs:
    Simuation duration
    List of frequencies
"""

import random
from collections import defaultdict
from typing import List

def run_simulation(duration: float, frequencies: List[float]):
    sum_freq = sum(frequencies)
    avg_time_between_events = 1.0 / sum_freq

    cur_time = 0.0
    counts = defaultdict(int)
    while cur_time < duration:
        r = random.uniform(0, sum_freq)
        for i, f in enumerate(frequencies):
            if r < f/sum_freq:
                print("Event {} fired at {}".format(i, round(cur_time, 1)))
                counts[f] += 1
                cur_time += avg_time_between_events

    print("\nactual event frequences:")
    for i, f in enumerate(frequencies):
        print("Event {} occured {} times at {} Hz".format(i, counts[f], counts[f]/duration))
                

# TODO need to return exact distribution, not just randomized
run_simulation(100.0, [1.0, 3.0, 6.0])

"""
Sample runs:


nate:misc$ python3 toy-problems/2022-12-15/question1.py 
Event 2 fired at 0.0
Event 0 fired at 0.1
Event 1 fired at 0.2
Event 2 fired at 0.30000000000000004
Event 0 fired at 0.4
Event 1 fired at 0.5
Event 2 fired at 0.6
Event 1 fired at 0.7
Event 2 fired at 0.7999999999999999
Event 1 fired at 0.8999999999999999
Event 2 fired at 0.9999999999999999

2, 4, 5 (count: 11)

nate:misc$ python3 toy-problems/2022-12-15/question1.py
Event 1 fired at 0.0
Event 2 fired at 0.1
Event 0 fired at 0.2
Event 1 fired at 0.30000000000000004
Event 2 fired at 0.4
Event 2 fired at 0.5
Event 2 fired at 0.6
Event 2 fired at 0.7
Event 2 fired at 0.7999999999999999
Event 2 fired at 0.8999999999999999
Event 1 fired at 0.9999999999999999
Event 2 fired at 1.0999999999999999

1, 3, 8 (count: 12)

nate:misc$ python3 toy-problems/2022-12-15/question1.py
Event 0 fired at 0.0
Event 1 fired at 0.1
Event 2 fired at 0.2
Event 1 fired at 0.30000000000000004
Event 2 fired at 0.4
Event 1 fired at 0.5
Event 2 fired at 0.6
Event 0 fired at 0.7
Event 1 fired at 0.7999999999999999
Event 2 fired at 0.8999999999999999
Event 2 fired at 0.9999999999999999

2, 4, 5 (count: 12)

nate:misc$ python3 toy-problems/2022-12-15/question1.py
Event 2 fired at 0.0
Event 1 fired at 0.1
Event 2 fired at 0.2
Event 2 fired at 0.30000000000000004
Event 0 fired at 0.4
Event 1 fired at 0.5
Event 2 fired at 0.6
Event 0 fired at 0.7
Event 1 fired at 0.7999999999999999
Event 2 fired at 0.8999999999999999
Event 2 fired at 0.9999999999999999

2, 3, 6 (count: 11)
"""
