import copy
import time

class GobbletEngine:
    def __init__(self, board, supply1, supply2, current_player):
        self.board = board  # 2D list: each cell is a list (the stack)
        self.supply1 = supply1  # List of pieces for player 1
        self.supply2 = supply2  # List of pieces for player 2
        self.current_player = current_player  # 1 or 2

    def evaluate(self):
        # A very simplified evaluation function.
        # In a real engine, you’d count potential winning lines,
        # board control, or other heuristics.
        return 0

    def generate_moves(self):
        moves = []
        player = self.current_player

        # Moves from supply:
        supply = self.supply1 if player == 1 else self.supply2
        for piece in supply:
            if not piece['used']:
                # Try placing this piece on every cell if legal
                for r in range(len(self.board)):
                    for c in range(len(self.board[0])):
                        cell = self.board[r][c]
                        if not cell or piece['size'] > cell[-1]['size']:
                            moves.append({
                                'type': 'supply',
                                'piece': piece,
                                'to': (r, c)
                            })

        # Moves from board: pick up your own top piece and place it elsewhere.
        for r in range(len(self.board)):
            for c in range(len(self.board[0])):
                cell = self.board[r][c]
                if cell and cell[-1]['player'] == player:
                    piece = cell[-1]
                    # Try moving it to another cell
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
        # Make a deep copy of the current state and apply the move.
        new_engine = copy.deepcopy(self)
        if move['type'] == 'supply':
            # Mark the piece as used in supply.
            supply = new_engine.supply1 if move['piece']['player'] == 1 else new_engine.supply2
            for p in supply:
                if p['id'] == move['piece']['id']:
                    p['used'] = True
                    break
        elif move['type'] == 'board':
            # Remove the piece from its original cell.
            r, c = move['from']
            new_engine.board[r][c].pop()
        # Place the piece on the destination cell.
        r_to, c_to = move['to']
        new_engine.board[r_to][c_to].append({
            'player': move['piece']['player'],
            'size': move['piece']['size'],
            'id': move['piece']['id']
        })
        return new_engine

    def minimax(self, depth, alpha, beta, maximizing_player, deadline):
        if time.time() > deadline:
            return {'score': 0}  # Time's up, return a neutral score.

        moves = self.generate_moves()
        if depth == 0 or not moves:
            return {'score': self.evaluate()}

        best_move = None
        if maximizing_player:
            max_eval = float('-inf')
            for move in moves:
                new_state = self.apply_move(move)
                # Switch player for next state:
                new_state.current_player = 2 if self.current_player == 1 else 1
                eval_result = new_state.minimax(depth - 1, alpha, beta, False, deadline)
                if eval_result['score'] > max_eval:
                    max_eval = eval_result['score']
                    best_move = move
                alpha = max(alpha, eval_result['score'])
                if beta <= alpha or time.time() > deadline:
                    break
            return {'score': max_eval, 'move': best_move}
        else:
            min_eval = float('inf')
            for move in moves:
                new_state = self.apply_move(move)
                new_state.current_player = 2 if self.current_player == 1 else 1
                eval_result = new_state.minimax(depth - 1, alpha, beta, True, deadline)
                if eval_result['score'] < min_eval:
                    min_eval = eval_result['score']
                    best_move = move
                beta = min(beta, eval_result['score'])
                if beta <= alpha or time.time() > deadline:
                    break
            return {'score': min_eval, 'move': best_move}

def iterative_deepening(engine, time_limit):
    # If the board is completely empty, choose the fixed first move.
    board_empty = all(not cell for row in engine.board for cell in row)
    if board_empty:
        supply = engine.supply1 if engine.current_player == 1 else engine.supply2
        # Look for a piece with size 4 ("big") that is not used.
        for piece in supply:
            if piece['size'] == 4 and not piece['used']:
                return {
                    'type': 'supply',
                    'piece': piece,
                    'to': (1, 2)  # (row 1, column 2) == 2nd down, 3rd across (if indexing from 0)
                }

    # Otherwise, perform iterative deepening search.
    import time
    deadline = time.time() + time_limit
    best_move = None
    depth = 1
    while time.time() < deadline:
        result = engine.minimax(depth, float('-inf'), float('inf'), True, deadline)
        if result and result.get('move'):
            best_move = result['move']
        depth += 1
        if abs(result.get('score', 0)) == float('inf'):
            break
    return best_move


if __name__ == '__main__':
    # Example initialization:
    # Create a 4x4 board, where each cell starts as an empty list.
    board = [[[] for _ in range(4)] for _ in range(4)]

    # Function to create a player's supply: 3 pieces of each size 1,2,3,4.
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

    # Start with Player 1's turn.
    engine = GobbletEngine(board, supply1, supply2, 1)

    # Let the engine choose a move within a 10-second time limit.
    best_move = iterative_deepening(engine, 10)
    print("Best move found:", best_move)
