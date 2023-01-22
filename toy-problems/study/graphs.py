from collections import defaultdict, deque

"""
Implementation below borrowed from

https://www.geeksforgeeks.org/python-program-for-breadth-first-search-or-bfs-for-a-graph/
https://www.geeksforgeeks.org/python-program-for-depth-first-search-or-dfs-for-a-graph/
"""

class Graph(object):

    def __init__(self):
        self.graph = defaultdict(list)

    def add_edge(self, u, v):
        self.graph[u].append(v)

    def BFS(self, s):
        q, visited = deque([s]), []
        has_cycle = False
        while q:
            v = q.popleft()
            if v in visited:
                has_cycle = True
                continue
            visited.append(v)
            for n in self.graph[v]:
                q.append(n)

        return visited, has_cycle


    def DFS(self, s):
        q, visited = deque([s]), []
        has_cycle = False
        while q:
            v = q.popleft()
            if v in visited:
                has_cycle = True
                continue
            visited.append(v)
            for n in self.graph[v]:
                q.appendleft(n)

        return visited, has_cycle


g = Graph()
g.add_edge(0, 1)
g.add_edge(0, 2)
g.add_edge(1, 2)
g.add_edge(1, 4)
g.add_edge(2, 0)
g.add_edge(2, 3)
g.add_edge(2, 5)
g.add_edge(3, 3)
g.add_edge(5, 6)
#print(g.graph)
#print("")
print(g.BFS(2))
print(g.DFS(2))

del g

g = Graph()
g.add_edge("a","b")
g.add_edge("a","c")
g.add_edge("b","a")
g.add_edge("b","d")
g.add_edge("c","a")
g.add_edge("c","d")
g.add_edge("d","e")
g.add_edge("e","a")
print(g.BFS("a"))
print(g.DFS("a"))


"""
Here is another implementation that uses an upfront constructor arg input
for the full graph instead of adding edges one by one

https://www.tutorialspoint.com/python_data_structure/python_graph_algorithms.htm
"""

class Graph2:

    def __init__(self,gdict=None):
      if gdict is None:
         gdict = {}
      self.gdict = gdict
    
    def BFS(self, start):
        seen, queue = set([start]), deque([start])
        while queue:
            v = queue.popleft()
            seen.add(v)
            for node in self.gdict[v]: # TODO debug why this might throw KeyError 
                if node not in seen:
                    queue.append(node)
        return seen

    def DFS(self, start, visited = None):
        """
        Check for the visisted and unvisited nodes
        Note that this is a recursive implementation
        """
        visited = set()
        visited.add(start)
        # print(start)
        for next in self.gdict[start] - visited:
            self.DFS(next, visited) # TODO debug why this might throw RecursionError
        return visited


gdict1 = {
    0: set([1,2]),
    1: set([2,4]),
    2: set([0,3,5]),
    3: set([3]),
    5: set([6]),
}

gdict2 = { 
    "a" : set(["b","c"]),
    "b" : set(["a", "d"]),
    "c" : set(["a", "d"]),
    "d" : set(["e"]),
    "e" : set(["a"])
}

#g = Graph2(gdict2)
#print(g.BFS("a"))
#print(g.DFS("a"))

