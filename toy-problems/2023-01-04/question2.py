"""
Suppose you are building a module for measuring the health of physical appliances. You may want to measure network bandwidth, CPU usage and memory. Assume there is a system monitoring daemon that calls the update() method periodically in the following class.

We are interested in the average statistics within a window of time. Remember that update/average may be called at arbitrary intervals. You may assume that timestamps are monotonically non-decreasing.
"""
import time

class Stats(object):

    def __init__(self, time_window):
        # time_window: window in seconds to consider
        self.metrics = []
        self.time_window = time_window

    def update(self, metric):
        timestamp = time.time()
        self.metrics.append([timestamp, metric])
        # metric: numeric value
        # timestamp: output of time.time()
    
    def average(self):
        # Returns average in window
        now = time.time()
        earliest = now - self.time_window

        arr = []
        for m in self.metrics:
            if m[0] >= earliest:
                arr.append(m[1])

        print(arr)
        if len(arr) > 0:
            return sum(arr) / len(arr)
        return 0.0

    def cleanup(self):
        now = time.time()
        earliest = now - self.time_window
        
        tmp = self.metrics[:]
        cur = -1
        for ix, m in enumerate(tmp):
            if m[0] < earliest:
                cur = ix
        self.metrics = tmp[cur:]

# Example usage

"""
stats.average should return the average of all the
metric values on the interval

[timestamp-time_window, timestamp]
"""



s1 = Stats(1.1)
time.sleep(0.5)
s1.update(50.0)
time.sleep(0.5)
s1.update(70.0)
time.sleep(0.5)
s1.update(80.0)
time.sleep(0.5)
s1.update(60.0)

#print(s1.metrics)
#print(s1.average()) # expects 70

#s1.average(4.1) # == [1.1, 4.1] == avg(70, 80, 60) == 70

s2 = Stats(1.0)
s2.update(60.0)
s2.update(80.0)
print(s2.time_window)
print(s2.metrics)
print(s2.average()) # 70



stats = Stats(0)
stats.update(60.0)
stats.update(80.0)
print(stats.average()) # 0


stats = Stats(-1)
stats.update(60.0)
stats.update(80.0)
print(stats.average()) # 0
