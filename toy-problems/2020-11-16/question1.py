"""
0 - 1M

1. Reserve(id)
2. ReserveAny()
3. Check(id)

Worst case time complexity: O(1) for all 3 => Bloom Filter (duh! 17 hours later)

Other notes:
* don't have to worry thread safety
* return False if ID is outside range
* should use arithmetic based function for O(1) time
* use a linked list
"""

import random

class ReservationServiceLinear:
  
  def __init__(self):
    self.reservations = []
    
  """
  Reserve will return True if the id is available for reservation
  and can be reserved by the caller, False otherwise. Once reserved,
  the ID is no longer available for reservation
  """
  def reserve(self, id):
    if id < 0 or id > 1e6:
        return False

    if self.check(id):
        return False

    self.reservations.append(id)
    return True

  """
  ReserveAny will return a random int between 0 and 1M, once reserved
  the ID is no longer available for reservation
  """
  def reserve_any(self):
    # () -> int
    r = 0
    while not self.reserve(r):
        r = random.randint(0,1e6)

    return True

  """
  Check will return True if the id is already reserved, False otherwise. 
  This operation will not change any state.
  """
  def check(self, id):
    # (int) -> bool
    return id in self.reservations

r = ReservationServiceLinear()
print r.reserve(1)
print r.reserve_any()
print r.reserve_any()
print r.reserve_any()
print r.reserve(-1)
print r.reserve(2e6)
print r.reservations



class ReservationServiceBloomFilter:

    def __init__(self):
        pass

    def check(self, id):
        pass

    def reserve(self, id):
        pass

    def reserve_any(self):
        pass
