from collections import defaultdict, deque

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
#g.add_edge(1, 2)
g.add_edge(1, 4)
#g.add_edge(2, 0)
g.add_edge(2, 3)
g.add_edge(2, 5)
g.add_edge(3, 3)
g.add_edge(5, 6)
 
print(g.graph)
print("")

print(g.BFS(2))
print(g.DFS(2))

