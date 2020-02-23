# ======================================================================
# FILE:        MyAI.py
#
# AUTHOR:      Abdullah Younis
#              Alexander Mulligan
#
# DESCRIPTION: This file contains your agent class, which you will
#              implement. You are responsible for implementing the
#              'getAction' function and any helper methods you feel you
#              need.
#
# NOTES:       - If you are having trouble understanding how the shell
#                works, look at the other parts of the code, as well as
#                the documentation.
#
#              - You are only allowed to make changes to this portion of
#                the code. Any changes to other portions of the code will
#                be lost when the tournament runs your code.
# ======================================================================

from Agent import Agent
from collections import defaultdict
from queue import LifoQueue, Queue

class MyAI ( Agent ):

    def __init__ ( self ):
        # ======================================================================
        # YOUR CODE BEGINS
        # ======================================================================
        self.x = 1
        self.y = 1
        self.visitedNodes = set() #keeps track of visited nodes
        self.safeNodes = set() #keeps track of safe nodes
        self.moveLists = defaultdict(list)
        self.map = self.Graph()
        self.hasArrow = True
        self.hasGold = False
        self.orientation = "right" #right, left, up, down
        self.lastAction = Agent.Action.CLIMB
        self.boundaryX = 4
        self.boundaryY = 4
        self.worldKnowledge = [[None for x in range(7)] for y in range(7)]
        self.actionQueue = Queue() #for multi-step actions
        self.parents = defaultdict(tuple)
        # ======================================================================
        # YOUR CODE ENDS
        # ======================================================================

    def getAction( self, stench, breeze, glitter, bump, scream ):
        # ======================================================================
        # YOUR CODE BEGINS
        # ======================================================================
        prev_pos = self.x, self.y
        self.update_orient(self.lastAction)
        self.update_pos(self.lastAction)
        
        # handle the conner case at (1,1) if breeze or stench.
        if self.x == 1 and self.y == 1:
            if self.lastAction == Agent.Action.CLIMB:
                if breeze:
                    self.lastAction = Agent.Action.CLIMB
                    return Agent.Action.CLIMB
                if stench:
                    self.lastAction = Agent.Action.SHOOT
                    return Agent.Action.SHOOT
            if self.lastAction == Agent.Action.SHOOT:
                self.hasArrow = False
                for x in range(7):
                    for y in range(7):
                        if not self.worldKnowledge[y][x]:
                            self.worldKnowledge[y][x] = self.Node()
                        self.worldKnowledge[y][x].wumpus = False
                if not scream:
                    self.worldKnowledge[self.y-1][self.x].wumpus = True
                    self.lastAction = Agent.Action.TURN_LEFT
                    return Agent.Action.TURN_LEFT
                if scream:
                    self.lastAction = Agent.Action.FORWARD
                    return Agent.Action.FORWARD
        
        if not (self.x, self.y) == prev_pos and not self.parents[prev_pos] == (self.x, self.y):
            self.parents[(self.x, self.y)] = prev_pos
        #print(f'pos: {self.x}, {self.y}')
        if not self.actionQueue.empty():
            next_move = self.actionQueue.get_nowait()
            self.lastAction = next_move
            return next_move
        if glitter:
            self.hasGold = True
            self.lastAction = Agent.Action.GRAB
            return Agent.Action.GRAB
        if bump:
            pass
        else:
            self.tell(self.x-1, self.y-1, stench, breeze, glitter)
            self.mark_visited(self.x-1, self.y-1)
            if (self.x, self.y) not in self.visitedNodes:
                self.DLS()
            move = self.chooseMove()
            #print(f"safe: {self.safeNodes}")
            #print(f"visited: {self.visitedNodes}")
            #print(f"move: {move}")
            self.visitedNodes.add((self.x, self.y))
            if move == ():
                self.lastAction = Agent.Action.CLIMB
                return Agent.Action.CLIMB
            self.move_to(move[0], move[1])
            act = self.actionQueue.get_nowait()
            self.lastAction = act
            return act
            
        self.lastAction = Agent.Action.CLIMB
        return Agent.Action.CLIMB
        # ======================================================================
        # YOUR CODE ENDS
        # ======================================================================
    
    # ======================================================================
    # YOUR CODE BEGINS
    # ======================================================================
    def update_pos(self, action):
        if action == Agent.Action.FORWARD:
            if self.orientation == 'up':
                self.y += 1
            if self.orientation == 'down':
                self.y -= 1
            if self.orientation == 'right':
                self.x += 1
            if self.orientation == 'left':
                self.x -= 1
    
    def update_orient(self, action):
        o = ['up', 'right', 'down', 'left']
        n = o.index(self.orientation)
        if action == Agent.Action.TURN_LEFT:
            self.orientation = o[n-1]
        if action == Agent.Action.TURN_RIGHT:
            if n+1 > 3:
                c = 0
            else:
                c = n+1
            self.orientation = o[c]
    
    def DLS(self):
        c = [(self.x+1,self.y), (self.x, self.y+1), (self.x-1, self.y), (self.x, self.y-1)]
        for x,y in c:
            if self.boundaryX >= x > 0 and self.boundaryY >= y > 0:
                self.moveLists[(self.x, self.y)].append((x,y))
                
    def chooseMove(self):
        for t in self.moveLists[(self.x, self.y)]:
            if t not in self.visitedNodes and t in self.safeNodes:
                return t
        return self.parents[(self.x, self.y)]
    
    def tell(self, x, y, stench, breeze, glitter):
        if self.boundaryX > x >= 0 and self.boundaryY > y >= 0:
            if not self.worldKnowledge[y][x]:
                self.worldKnowledge[y][x] = self.Node()
            self.worldKnowledge[y][x].update(stench, breeze, glitter)
            self.propagate_knowledge(x, y)
        
    def update_tile(self, x, y, stench, breeze):
        if self.boundaryX > x >= 0 and self.boundaryY > y >= 0:
            if not self.worldKnowledge[y][x]:
                self.worldKnowledge[y][x] = self.Node()
            if self.worldKnowledge[y][x].visited:
                return
            wumpus = False
            pit =  False
            
            # If wumpus is False then it is sure there is no wumpus
            # but wumpus is True, it does not mean it has a wumpus for sure e.g. if no square of it has discovered.
            # it all of the neighbors (actually, two of the neighbors are enough) have been discovred, 
            # then if wumpus is True, it has a wumpus for sure.
            if stench:
                wumpus = True
                if self.worldKnowledge[y][x-1]:
                    if not self.worldKnowledge[y][x-1].stench:
                        wumpus = False
                elif self.worldKnowledge[y][x+1]:
                    if not self.worldKnowledge[y][x+1].stench:
                        wumpus = False
                elif self.worldKnowledge[y-1][x]:
                    if not self.worldKnowledge[y-1][x].stench:
                        wumpus = False
                elif self.worldKnowledge[y+1][x]:
                    if not self.worldKnowledge[y+1][x].stench:
                        wumpus = False
            
            # If pit is False then it is sure there is no pit
            # but pit is True, it does not mean it has a pit for sure.
            if breeze:
                pit = True
                if self.worldKnowledge[y][x-1]:
                    if not self.worldKnowledge[y][x-1].breeze:
                        pit = False
                elif self.worldKnowledge[y][x+1]:
                    if not self.worldKnowledge[y][x+1].breeze:
                        pit = False
                elif self.worldKnowledge[y-1][x]:
                    if not self.worldKnowledge[y-1][x].breeze:
                        pit = False
                elif self.worldKnowledge[y+1][x]:
                    if not self.worldKnowledge[y+1][x].breeze:
                        pit = False
            
            if not self.worldKnowledge[y][x].wumpus:
                wumpus = False
            if not self.worldKnowledge[y][x].pit:
                pit = False
            
            self.worldKnowledge[y][x].infer(wumpus, pit)
            if self.worldKnowledge[y][x].safe:
                self.safeNodes.add((x+1, y+1))
            else:
                if (x+1,y+1) in self.safeNodes:
                    self.safeNodes.remove((x+1, y+1))
        
    def propagate_knowledge(self, x, y):
        i = self.worldKnowledge[y][x]
        self.update_tile(x, y-1, i.stench, i.breeze)
        
        self.update_tile(x, y+1, i.stench, i.breeze)
        
        self.update_tile(x-1, y, i.stench, i.breeze)
        
        self.update_tile(x+1, y, i.stench, i.breeze)
        
            
    def mark_visited(self, x, y):
        self.worldKnowledge[y][x].visit()
        
    def ask(self, x, y):
        return self.worldKnowledge[y][x].safe
    
    def back(self):
        if self.nodeHistory:
            b = self.nodeHistory.get_nowait()
            self.actionQueue.put_nowait(Agent.Action.TURN_RIGHT)
            self.actionQueue.put_nowait(Agent.Action.TURN_RIGHT)
            self.actionQueue.put_nowait(self.actionStack.get_nowait())
    
    def move_to(self, x, y):
        if x == self.x:
            if y > self.y:
                self.orient('up')
                self.actionQueue.put_nowait(Agent.Action.FORWARD)
            elif y < self.y:
                self.orient('down')
                self.actionQueue.put_nowait(Agent.Action.FORWARD)
        elif y == self.y:
            if x > self.x:
                self.orient('right')
                self.actionQueue.put_nowait(Agent.Action.FORWARD)
            elif x < self.x:
                self.orient('left')
                self.actionQueue.put_nowait(Agent.Action.FORWARD)
        
    def orient(self, direction):
        if not self.orientation == direction:
            if direction == 'up':
                if self.orientation == 'right':
                    self.actionQueue.put_nowait(Agent.Action.TURN_LEFT)
                elif self.orientation == 'left':
                    self.actionQueue.put_nowait(Agent.Action.TURN_RIGHT)
                else:
                    self.actionQueue.put_nowait(Agent.Action.TURN_LEFT)
                    self.actionQueue.put_nowait(Agent.Action.TURN_LEFT)
            elif direction == 'right':
                if self.orientation == 'down':
                    self.actionQueue.put_nowait(Agent.Action.TURN_LEFT)
                elif self.orientation == 'up':
                    self.actionQueue.put_nowait(Agent.Action.TURN_RIGHT)
                else:
                    self.actionQueue.put_nowait(Agent.Action.TURN_LEFT)
                    self.actionQueue.put_nowait(Agent.Action.TURN_LEFT)
            elif direction == 'left':
                if self.orientation == 'up':
                    self.actionQueue.put_nowait(Agent.Action.TURN_LEFT)
                elif self.orientation == 'down':
                    self.actionQueue.put_nowait(Agent.Action.TURN_RIGHT)
                else:
                    self.actionQueue.put_nowait(Agent.Action.TURN_LEFT)
                    self.actionQueue.put_nowait(Agent.Action.TURN_LEFT)
            else:
                if self.orientation == 'left':
                    self.actionQueue.put_nowait(Agent.Action.TURN_LEFT)
                elif self.orientation == 'right':
                    self.actionQueue.put_nowait(Agent.Action.TURN_RIGHT)
                else:
                    self.actionQueue.put_nowait(Agent.Action.TURN_LEFT)
                    self.actionQueue.put_nowait(Agent.Action.TURN_LEFT)
            
    class Node(object):
        '''Node object storing all the information about a node'''
        def __init__(self):
            self.stench = True
            self.breeze = True
            self.glitter = False
            self.visited = False
            self.safe = False
            self.wumpus = True
            self.pit = True
            
        def __bool__(self):
            return self.safe
                
        def update(self, stench, breeze, glitter):
            self.stench = stench
            self.breeze = breeze
            self.glitter = glitter
                
        def infer(self, wumpus, pit):
            if not self.visited:
                self.wumpus = wumpus
                self.pit = pit
                self.safe = not (self.wumpus or self.pit)
                    
        def visit(self):
            self.visited = True
    
    class Graph(object):
        '''Simple directed graph object'''
        def __init__(self):
            self._graph = defaultdict(set)
        def add_connections(self, connections):
            for n1,n2 in connections:
                self.add(n1,n2)
        def add(self, n1, n2):
            self._graph[n1].add(n2)
            #self._graph[n2].add(n1)
        def connected(self, n1, n2):
            return n1 in self._graph and n2 in self._graph[n1]
        def path(self, n1, n2, path = []):
            path = path + n1
            if n1 == n2:
                return path
            if n1 not in self._graph:
                return None
            for n in self._graph[n1]:
                if n not in path:
                    updated_path = self.path(n, n2, path)
                    if updated_path:
                        return updated_path
            return None
        def __str__(self):
            return 'Graph: {}'.format(dict(self._graph))
            
            
    # ======================================================================
    # YOUR CODE ENDS
    # ======================================================================
    
