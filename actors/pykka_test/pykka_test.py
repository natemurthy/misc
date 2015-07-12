import pykka
import time

class Counter(pykka.ThreadingActor):
	def __init__(self):
		super(Counter,self).__init__()
		self.counter = 0

	def on_receive(self, msg):
		self.counter = msg['i']

if __name__ == '__main__':
	N = 1000000
	ref = Counter.start()
	start = time.time()
	for i in range(N): ref.tell({'i':i})
	end = time.time()
	ref.stop()
	print("Time to process %d messages: %f s" % (N,end-start))
