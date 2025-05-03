"""
https://www.tutorialspoint.com/python_data_structure/python_graph_algorithms.htm
"""
import collections

class graph: # unused
   def __init__(self,gdict=None):
      if gdict is None:
         gdict = {}
      self.gdict = gdict

def bfs(graph, startnode):
   # Track the visited and unvisited nodes using queue
   seen, queue = set([startnode]), collections.deque([startnode])
   while queue:
      vertex = queue.popleft()
      marked(vertex)
      for node in graph[vertex]:
         if node not in seen:
            seen.add(node)
            queue.append(node)

def dfs(graph, start, visited = None):
   if visited is None:
      visited = set()
   visited.add(start)
   print(start)
   for next in graph[start] - visited:
      dfs(graph, next, visited)
   return visited

def marked(n):
   print(n)

# The graph dictionary
gdict = { 
   'a' : set(['b','c']),
   'b' : set(['a', 'd']),
   'c' : set(['a', 'd']),
   'd' : set(['e']),
   'e' : set(['a'])
}
#bfs(gdict, 'a')
dfs(gdict, 'a')
