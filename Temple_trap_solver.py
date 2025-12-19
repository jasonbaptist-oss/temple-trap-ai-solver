from typing import List,Tuple,Dict,Set
from collections import deque
import heapq
import copy
#↑, ↓, ←, →

class Tile():
    def __init__(self,name,top_opens,ground_opens,hole,stairs,symbol):
        self.name=name
        self.top_opens=top_opens
        self.ground_opens=ground_opens
        self.hole=hole
        self.stairs=stairs
        self.symbol=symbol

TILES = {
    'A': Tile('A', {1, 2}, set(), False, False,'='),
    'B': Tile('B', {1, 2}, set(), False, False,'◽️'),
    'C': Tile('C', {2, 4}, set(), False, False,'+'),
    'D': Tile('D', {4}, {2}, True, True,'◆'),
    'E': Tile('E', {4}, {2}, True, True,'*'),
    'F': Tile('F', set(), {1, 2}, True, False,'▷'),
    'G': Tile('G', set(), {1, 2}, True, False,'x'),
    'H': Tile('H', set(), {1, 2}, True, False,'⚪️'),
}

TILES_COPY = {
    'A': Tile('A', {1, 2}, set(), False, False,'='),
    'B': Tile('B', {1, 2}, set(), False, False,'◽️'),
    'C': Tile('C', {2, 4}, set(), False, False,'+'),
    'D': Tile('D', {4}, {2}, True, True,'◆'),
    'E': Tile('E', {4}, {2}, True, True,'*'),
    'F': Tile('F', set(), {1, 2}, True, False,'▷'),
    'G': Tile('G', set(), {1, 2}, True, False,'x'),
    'H': Tile('H', set(), {1, 2}, True, False,'⚪️'),
}

 
ROWS=3
COLS=3

neighbors={
0:{1:2,3:3},
1:{0:4,2:2,4:3},
2:{1:4,5:3},
3:{0:1,4:2,6:3},
4:{1:1,5:2,7:3,3:4},
5:{2:1,8:3,4:4},
6:{3:1,7:2},
7:{4:1,8:2,6:4},
8:{5:1,7:4}
}


class State():
    def __init__(self,board,pos,layer):
        # copy board to avoid accidental shared-list mutation
        self.board=list(board)
        self.pawn_pos=pos
        self.pawn_layer=layer

    def __str__(self):
        lines=[]
        for i in range(ROWS):
            lines.append(' '.join(self.board[i*ROWS:(i+1)*ROWS]))
        return '\n'.join(lines)

    def __lt__(self,other):
        # required by heapq when f-scores tie; return arbitrary but deterministic
        return (self.pawn_pos, self.pawn_layer, tuple(self.board)) < (other.pawn_pos, other.pawn_layer, tuple(other.board))

    def __eq__(self, other):
        return isinstance(other, State) and self.pawn_pos==other.pawn_pos and self.pawn_layer==other.pawn_layer and self.board==other.board

    def __hash__(self):
        return hash((tuple(self.board), self.pawn_pos, self.pawn_layer))
    
class TempleTrap():
    def __init__(self,state,rotations):
        self.initial_state=state
        self.rotations=rotations

        # apply rotations to the TILES dict (create rotated copies)
        for i in range(len(self.rotations)):
            rot = self.rotations[i]
            if rot == 0:
                continue
            name=self.initial_state.board[i]
            tile=TILES[name]
            # compute rotated top and ground openings (if present)
            if tile.top_opens:
                new_top_opens=set()
                for j in tile.top_opens:
                    value = ((j - rot + 4) % 4)
                    value=value if value>0 else 4
                    new_top_opens.add(value if value>0 else 4)
            else:
                new_top_opens = set(tile.top_opens)

            if tile.ground_opens:
                new_ground_opens=set()
                for j in tile.ground_opens:
                    value = ((j - rot + 4) % 4)
                    value =value if value>0 else 4
                    new_ground_opens.add(value if value>0 else 4)
            else:
                new_ground_opens = set(tile.ground_opens)

            TILES_COPY[name] = Tile(tile.name, new_top_opens, new_ground_opens, tile.hole, tile.stairs,tile.symbol)

    def reachable_cell(self,state: State):
        reachable=set()
        queue=deque()
        reachable_cost=set()
        initial=(state.pawn_pos,state.pawn_layer,0,'')
        queue.append(initial)
        visited=set()
        visited.add((state.pawn_pos,state.pawn_layer))
        reachable_path=set()


        while queue:
            cell,floor,cost,path=queue.popleft()
            reachable.add((cell,floor))
            reachable_cost.add((cell,floor,cost))
            reachable_path.add((cell,floor,cost,path))

            # if there's no tile at this cell, cannot move from here
            if state.board[cell]==' ':
                continue
            
            tile=TILES_COPY[state.board[cell]]
            # stairs allow switching layers
            if tile.stairs:
                other_layer='ground' if floor=='top' else 'top'
                if (cell,other_layer) not in visited:
                    queue.append((cell,other_layer,cost,path))
                    visited.add((cell,other_layer))

            # explore neighbors on same layer
            for nbr,open_side in neighbors[cell].items():
                opens = tile.top_opens if floor=='top' else tile.ground_opens
                if state.board[nbr]==' ':
                    continue
                nbr_tile = TILES_COPY[state.board[nbr]]
                neighbor_opens = nbr_tile.top_opens if floor=='top' else nbr_tile.ground_opens
                opposite_openings={1:3,2:4,3:1,4:2}
                if open_side in opens and opposite_openings[open_side] in neighbor_opens:
                    #print(f'visited is {visited} ')
                    if (nbr,floor) not in visited:
                       #print(f' addded is {(nbr,floor)}')
                        visited.add((nbr,floor))
                        if open_side==1:
                            queue.append((nbr,floor,cost+1,path+'↑'))
                        #↓, ←, →
                        elif open_side==2:
                            queue.append((nbr,floor,cost+1,path+'→'))

                        elif open_side==3:
                            queue.append((nbr,floor,cost+1,path+'↓'))

                        elif open_side==4:
                            queue.append((nbr,floor,cost+1,path+'←'))
                        
                
        return reachable,reachable_cost,reachable_path
    


    def goal_reachable(self,state: State):
        reachable,reachable_cost,reachable_path=self.reachable_cell(state)
        
        # if goal cell (0) not reachable on any layer, return False
        if (0,'top') not in reachable and (0,'ground') not in reachable:
            return False
        
        tile=TILES_COPY[state.board[0]]

        # if any reachable (0,layer) has opening 4 (exit) on that layer, goal reachable
        for cell,floor,cost,path in reachable_path:
            if cell==0:
                if floor=='ground':
                    return False
                opens = tile.top_opens
                if 4 in opens:
                    return True,cost,f'♔{path}'
        
        return False
    
    def get_children(self,state: State):
        """
        Returns list of (child_state, step_cost, action_description)
        """
        children=[]
        blank_pos=state.board.index(' ')
        reachable,reachable_cost,reachable_path=self.reachable_cell(state)
        #print(f' for state-{state.board} and pawn pos {state.pawn_pos} and layer {state.pawn_layer} reachable is\n {reachable_cost}')
        pawn_pos=state.pawn_pos
        pawn_layer = state.pawn_layer

        # pawn moves into hole tiles reachable
        for cell,floor,cost,path in reachable_path:
            if cell==pawn_pos:
                continue
            # if no tile at that cell or it's blank, skip
            if state.board[cell]==' ':
                continue
            tile=TILES_COPY[state.board[cell]]
            if tile.hole:
                new_board = list(state.board)
                # pawn moves to that cell (board unchanged)
                new_state = State(new_board, cell, floor)
                children.append((new_state,cost, f'p:{pawn_pos}->{cell}',f'♔{path} '))

        # move a tile into the blank from adjacent neighbor (if neighbor tile has hole)
        for nbr,open_side in neighbors[blank_pos].items():
            if nbr==pawn_pos:
                continue
            if state.board[nbr]==' ':
                continue
            tile=TILES_COPY[state.board[nbr]]
            #if tile.hole:
            new_board = list(state.board)
            new_board[blank_pos] = tile.name
            new_board[nbr] = ' '
            new_state = State(new_board, pawn_pos, pawn_layer)
            #↑, ↓, ←, →
            if open_side==1:
                children.append((new_state, 1, f't{nbr}->{blank_pos}',f'{tile.symbol}↓ '))

            elif open_side==2:
                children.append((new_state, 1, f't{nbr}->{blank_pos}',f'{tile.symbol}← '))

            elif open_side==3:
                children.append((new_state, 1, f't{nbr}->{blank_pos}',f'{tile.symbol}↑ '))

            elif open_side==4:
                children.append((new_state, 1, f't{nbr}->{blank_pos}',f'{tile.symbol}→ '))

            

        return children
    
    def heuristic(self,state: State):
        # trivial check: if goal is already reachable, heuristic 0
        if self.goal_reachable(state):
            return 0
        
        # manhattan distance from pawn to goal cell 0 (row/col)
        pawn_row, pawn_col = divmod(state.pawn_pos, ROWS)
        manhattan = abs(pawn_row - 0) + abs(pawn_col - 0)

        # small extra credit if exit (4) already present in tile 0's openings
        credit=0
        if state.board[0]!=' ':
            tile=TILES_COPY[state.board[0]]
            if 4 not in tile.ground_opens and 4 not in tile.top_opens:
                credit=1
        elif state.board[0]==' ':
            credit=1

        return manhattan + credit
    

    def solve(self):
        frontier=[]
        initial_state=self.initial_state
        initial_h=self.heuristic(initial_state)
        visited={initial_state:0}
        heapq.heappush(frontier,(initial_h,0,initial_state,[],''))
        nodes_explored=0
        while frontier:
            f_score,cost,state,path,movement=heapq.heappop(frontier)
            nodes_explored+=1
            #print(f'chosen point is {state.board} and {state.pawn_pos} and cost is {cost} and path is {path} with fscore-{f_score}')

            
            if self.goal_reachable(state):
                value,add_cost,step_path=self.goal_reachable(state)
                #print(f'state is {state.board} and pawn pos is {state.pawn_pos} and pawn layer is {state.pawn_layer} and add cost is {add_cost}')
                print(f'Solution found!!, No. of nodes explored={nodes_explored}')
                Total_cost=cost+add_cost+1
                final_path=movement+step_path+'←'
                print(f'Total_cost={cost+add_cost+1}')
                print(f'path is {movement+step_path+'←'}')
                return final_path,Total_cost
                
                
            
            # skip if we already found a better way to this state
            if state in visited and cost>visited[state]:
                continue

            children=self.get_children(state)
            for child,step_cost,action,step_path in children:
                
                new_cost=cost+step_cost
                #print(f'child want to be added is {child.board} ,{child.pawn_pos} and floor is {child.pawn_layer} cost is {new_cost} ')
                if child not in visited or visited[child]>new_cost:
                    #if child in visited:
                      #  print(f'child added is {child.board} ,{child.pawn_pos} and floor is {child.pawn_layer} cost is {new_cost} and prev cost was {visited[child]}')
                    #else:
                    #    print(f'child added is {child.board},{child.pawn_pos} and floor is {child.pawn_layer} and cost is{new_cost}')
                    visited[child]=new_cost
                    f_child = new_cost + self.heuristic(child)
                    heapq.heappush(frontier,(f_child,new_cost,child,path+[action],movement+step_path))
        print('No solution found')
        return None
    
    def solve_without_heuristic(self):
        frontier=[]
        initial_state=self.initial_state
        initial_h=self.heuristic(initial_state)
        visited={initial_state:0}
        heapq.heappush(frontier,(initial_h,0,initial_state,[],''))
        nodes_explored=0
        while frontier:
            f_score,cost,state,path,movement=heapq.heappop(frontier)
            if cost>15:
                break
            nodes_explored+=1
            #print(f'chosen point is {state.board} and {state.pawn_pos} and cost is {cost} and path is {path} with fscore-{f_score}')

            
            if self.goal_reachable(state):
                value,add_cost,step_path=self.goal_reachable(state)
                #print(f'state is {state.board} and pawn pos is {state.pawn_pos} and pawn layer is {state.pawn_layer} and add cost is {add_cost}')
                print(f'Solution found!!, No. of nodes explored={nodes_explored}')
                Total_cost=cost+add_cost+1
                final_path=movement+step_path+'←'
                print(f'Total_cost={cost+add_cost+1}')
                print(f'path is {movement+step_path+'←'}')
                return final_path,Total_cost
                
            
            # skip if we already found a better way to this state
            if state in visited and cost>visited[state]:
                continue

            children=self.get_children(state)
            for child,step_cost,action,step_path in children:
                
                new_cost=cost+step_cost
                #print(f'child want to be added is {child.board} ,{child.pawn_pos} and floor is {child.pawn_layer} cost is {new_cost} ')
                if child not in visited or visited[child]>new_cost:
                    #if child in visited:
                      #  print(f'child added is {child.board} ,{child.pawn_pos} and floor is {child.pawn_layer} cost is {new_cost} and prev cost was {visited[child]}')
                    #else:
                    #    print(f'child added is {child.board},{child.pawn_pos} and floor is {child.pawn_layer} and cost is{new_cost}')
                    visited[child]=new_cost
                    f_child = new_cost
                    heapq.heappush(frontier,(f_child,new_cost,child,path+[action],movement+step_path))
        print('No solution found')
        return None


# --- driver ---
print('-'*50)
initial_board=['C','D','G','B',' ','H','A','E','F']
rotations=[0,0,2,3,0,1,0,0,2]
pawn_pos=8
pawn_floor='ground'
initial_state=State(initial_board,pawn_pos,pawn_floor)
TT=TempleTrap(initial_state,rotations)
res = TT.solve()
print()
print(f'Solution found without heuristic is ->')
res=TT.solve_without_heuristic()


TILES_COPY.update(TILES)
print('\n'*4)
print('-'*50)
initial_board=['A','E','G','B',' ','D','H','C','F']
rotations=[2,1,0,0,0,0,0,2,2]
pawn_pos=1
pawn_floor='top'
initial_state=State(initial_board,pawn_pos,pawn_floor)
TT=TempleTrap(initial_state,rotations)
res=TT.solve()
print()
print(f'Solution found without heuristic is ->')
res=TT.solve_without_heuristic()


TILES_COPY.update(TILES)
print('\n'*4)
print('-'*50)

initial_board=['G','E','B','D','H','F','A',' ','C']
rotations=[2,3,1,0,1,0,0,0,3]
pawn_pos=1
pawn_floor='ground'
initial_state=State(initial_board,pawn_pos,pawn_floor)
TT=TempleTrap(initial_state,rotations)
res = TT.solve()
print()
print(f'Solution found without heuristic is ->')
res=TT.solve_without_heuristic()


TILES_COPY.update(TILES)
print('\n'*4)
print('-'*50)
initial_board=['B','D','H','E','G','F',' ','A','C']
rotations=[3,0,2,3,0,1,0,0,0]
pawn_pos=3
pawn_floor='ground'
initial_state=State(initial_board,pawn_pos,pawn_floor)
TT=TempleTrap(initial_state,rotations)
res = TT.solve()
print()
print(f'Solution found without heuristic is ->')
res=TT.solve_without_heuristic()


TILES_COPY.update(TILES)
print('\n'*4)
print('-'*50)
#MEDIUM

initial_board=['G','F','E','A','B','C','H',' ','D']
rotations=[2,3,1,2,3,3,0,0,3]
pawn_pos=6
pawn_floor='ground'
initial_state=State(initial_board,pawn_pos,pawn_floor)
TT=TempleTrap(initial_state,rotations)
res = TT.solve()
print()
print(f'Solution found without heuristic is ->')
res=TT.solve_without_heuristic()


TILES_COPY.update(TILES)
print('\n'*4)
print('-'*50)

initial_board=['C','E','G','F',' ','D','H','B','A']
rotations=[0,0,3,0,0,2,0,1,3]
pawn_pos=5
pawn_floor='top'
initial_state=State(initial_board,pawn_pos,pawn_floor)
TT=TempleTrap(initial_state,rotations)
res = TT.solve()
print()
print(f'Solution found without heuristic is ->')
res=TT.solve_without_heuristic()

TILES_COPY.update(TILES)
print('\n'*4)
print('-'*50)

initial_board=['C','A','B','D','E','G',' ','F','H']
rotations=[3,0,2,2,0,2,0,2,3]
pawn_pos=3
pawn_floor='top'
initial_state=State(initial_board,pawn_pos,pawn_floor)
TT=TempleTrap(initial_state,rotations)
res = TT.solve()
print()
print(f'Solution found without heuristic is ->')
res=TT.solve_without_heuristic()


TILES_COPY.update(TILES)
print('\n'*4)
print('-'*50)

initial_board=['G','H','C','B',' ','D','A','E','F']
rotations=[2,0,3,3,0,0,0,0,2]
pawn_pos=7
pawn_floor='top'
initial_state=State(initial_board,pawn_pos,pawn_floor)
TT=TempleTrap(initial_state,rotations)
res = TT.solve()
print()
print(f'Solution found without heuristic is ->')
res=TT.solve_without_heuristic()

TILES_COPY.update(TILES)
print('\n'*4)
print('-'*50)

#HARD

initial_board=['D','B','C','G','F','A','H','E',' ']
rotations=[3,2,3,0,2,1,1,1,0]
pawn_pos=0
pawn_floor='top'
initial_state=State(initial_board,pawn_pos,pawn_floor)
TT=TempleTrap(initial_state,rotations)
res = TT.solve()
print()
print(f'Solution found without heuristic is ->')
res=TT.solve_without_heuristic()


TILES_COPY.update(TILES)
print('\n'*4)
print('-'*50)

initial_board=['B','A','D','C','F','G',' ','H','E']
rotations=[2,0,3,0,2,3,0,1,1]
pawn_pos=4
pawn_floor='ground'
initial_state=State(initial_board,pawn_pos,pawn_floor)
TT=TempleTrap(initial_state,rotations)
res = TT.solve()
print()
print(f'Solution found without heuristic is ->')
res=TT.solve_without_heuristic()


TILES_COPY.update(TILES)
print('\n'*4)
print('-'*50)

initial_board=['C','A',' ','B','H','D','E','G','F']
rotations=[3,2,0,0,3,2,0,0,2]
pawn_pos=5
pawn_floor='ground'
initial_state=State(initial_board,pawn_pos,pawn_floor)
TT=TempleTrap(initial_state,rotations)
res = TT.solve()
print()
print(f'Solution found without heuristic is ->')
res=TT.solve_without_heuristic()


TILES_COPY.update(TILES)
print('\n'*4)
print('-'*50)

initial_board=['B','D','F','A','E','G','H','C',' ']
rotations=[3,0,2,0,0,2,0,3,0]
pawn_pos=5
pawn_floor='ground'
initial_state=State(initial_board,pawn_pos,pawn_floor)
TT=TempleTrap(initial_state,rotations)
res = TT.solve()
print()
print(f'Solution found without heuristic is ->')
res=TT.solve_without_heuristic()


TILES_COPY.update(TILES)
print('\n'*4)
print('-'*50)


initial_board=['E','B','G',' ','C','H','F','A','D']
rotations=[2,2,2,0,3,2,2,0,0]
pawn_pos=8
pawn_floor='top'
initial_state=State(initial_board,pawn_pos,pawn_floor)
TT=TempleTrap(initial_state,rotations)
res = TT.solve()
print()
print(f'Solution found without heuristic is ->')
res=TT.solve_without_heuristic()   

TILES_COPY.update(TILES)
print('\n'*4)
print('-'*50)

initial_board=['F','G','B',' ','H','E','D','C','A']
rotations=[3,2,2,0,0,2,2,0,1]
pawn_pos=0
pawn_floor='ground'
initial_state=State(initial_board,pawn_pos,pawn_floor)
TT=TempleTrap(initial_state,rotations)
res = TT.solve()
print()
print(f'Solution found without heuristic is ->')
res=TT.solve_without_heuristic()  
