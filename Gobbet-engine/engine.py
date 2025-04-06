import copy
import time
import random

class GobbletEngine:
    def __init__(self, board, supply1, supply2, current_player):
        self.board = board          # 2D list: each cell is a list (stack of pieces)
        self.supply1 = supply1      # List of pieces for player 1
        self.supply2 = supply2      # List of pieces for player 2
        self.current_player = current_player  # 1 or 2

    def generate_moves(self):
        moves = []
        player = self.current_player
        # Moves from supply: for each unused piece, try every board cell.
        supply = self.supply1 if player == 1 else self.supply2
        for piece in supply:
            if not piece['used']:
                for r in range(len(self.board)):
                    for c in range(len(self.board[0])):
                        cell = self.board[r][c]
                        if not cell or piece['size'] > cell[-1]['size']:
                            moves.append({
                                'type': 'supply',
                                'piece': piece,
                                'to': (r, c)
                            })
        # Moves from board: pick up your own top piece and try moving it.
        for r in range(len(self.board)):
            for c in range(len(self.board[0])):
                cell = self.board[r][c]
                if cell and cell[-1]['player'] == player:
                    piece = cell[-1]
                    for r2 in range(len(self.board)):
                        for c2 in range(len(self.board[0])):
                            if r == r2 and c == c2:
                                continue
                            dest = self.board[r2][c2]
                            if not dest or piece['size'] > dest[-1]['size']:
                                moves.append({
                                    'type': 'board',
                                    'piece': piece,
                                    'from': (r, c),
                                    'to': (r2, c2)
                                })
        return moves

    def apply_move(self, move):
        new_engine = copy.deepcopy(self)
        if move['type'] == 'supply':
            supply = new_engine.supply1 if move['piece']['player'] == 1 else new_engine.supply2
            for p in supply:
                if p['id'] == move['piece']['id']:
                    p['used'] = True
                    break
        elif move['type'] == 'board':
            r, c = move['from']
            new_engine.board[r][c].pop()
        r_to, c_to = move['to']
        new_engine.board[r_to][c_to].append({
            'player': move['piece']['player'],
            'size': move['piece']['size'],
            'id': move['piece']['id']
        })
        return new_engine

def get_move(engine, time_limit=10):
    # Wait for 'time_limit' seconds to simulate thinking.
    print("get_move called. Waiting for", time_limit, "seconds...")
    deadline = time.time() + time_limit
    while time.time() < deadline:
        time.sleep(0.1)
    moves = engine.generate_moves()
    print("Legal moves found:", moves)
    if moves:
        chosen_move = moves[0]
        print("Returning move:", chosen_move)
        return chosen_move
    print("No legal moves found.")
    return None

def create_engine_from_state(state):
    board = state['board']
    supply1 = state['supply1']
    supply2 = state['supply2']
    current_player = state['currentPlayer']
    return GobbletEngine(board, supply1, supply2, current_player)

if __name__ == '__main__':
    # For testing from command line.
    board = [[[] for _ in range(4)] for _ in range(4)]
    def create_supply(player):
        supply = []
        counter = 1
        for size in [1, 2, 3, 4]:
            for _ in range(3):
                supply.append({
                    'id': f'P{player}-{counter}',
                    'player': player,
                    'size': size,
                    'used': False
                })
                counter += 1
        return supply
    supply1 = create_supply(1)
    supply2 = create_supply(2)
    engine = GobbletEngine(board, supply1, supply2, 1)
    move = get_move(engine, 10)
    print("Move chosen:", move)
