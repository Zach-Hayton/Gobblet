import copy
import time
import random

####################################################
#                 ENGINE DEFINITION
####################################################

class GobbletEngine:
    def __init__(self, board, supply1, supply2, current_player):
        """
        board: 2D list (4x4 by default). board[r][c] is a list (stack) of pieces,
               each piece is dict: {'player':1 or 2, 'size':1..4, 'id':str}
        supply1, supply2: lists of piece dicts for each player
        current_player: integer (1 or 2)
        """
        self.board = board
        self.supply1 = supply1
        self.supply2 = supply2
        self.current_player = current_player

    def generate_moves(self):
        moves = []
        player = self.current_player
        supply = self.supply1 if player == 1 else self.supply2

        # Moves from supply: for each unused piece, try every board cell.
        for piece in supply:
            if not piece['used']:
                for r in range(len(self.board)):
                    for c in range(len(self.board[0])):
                        cell = self.board[r][c]
                        # We can place if stack is empty or top is smaller
                        if not cell or piece['size'] > cell[-1]['size']:
                            moves.append({
                                'type': 'supply',
                                'piece': piece,
                                'to': (r, c)
                            })

        # Moves from board: pick up your own top piece and try moving it elsewhere.
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
        """
        Returns a new GobbletEngine reflecting the position after 'move' is applied.
        """
        new_engine = copy.deepcopy(self)
        # Move from supply
        if move['type'] == 'supply':
            supply = new_engine.supply1 if move['piece']['player'] == 1 else new_engine.supply2
            for p in supply:
                if p['id'] == move['piece']['id']:
                    p['used'] = True
                    break
        # Move from board
        elif move['type'] == 'board':
            r, c = move['from']
            new_engine.board[r][c].pop()

        # Place piece on destination
        r_to, c_to = move['to']
        new_engine.board[r_to][c_to].append({
            'player': move['piece']['player'],
            'size': move['piece']['size'],
            'id': move['piece']['id']
        })

        # Switch current player
        new_engine.current_player = 1 if self.current_player == 2 else 2
        return new_engine


####################################################
#               HELPER FUNCTIONS
####################################################

def check_winner(board):
    """
    Returns 1 if player 1 has 4-in-a-row,
            2 if player 2 has 4-in-a-row,
            None otherwise.
    We only look at the top piece in each cell.
    """
    rows = len(board)
    cols = len(board[0])

    # Build top-grid
    top_grid = [[0]*cols for _ in range(rows)]
    for r in range(rows):
        for c in range(cols):
            if board[r][c]:
                top_grid[r][c] = board[r][c][-1]['player']
            else:
                top_grid[r][c] = 0

    def four_in_a_row(a,b,c,d):
        return a != 0 and a == b == c == d

    # rows
    for r in range(rows):
        if four_in_a_row(top_grid[r][0], top_grid[r][1], top_grid[r][2], top_grid[r][3]):
            return top_grid[r][0]
    # cols
    for c in range(cols):
        if four_in_a_row(top_grid[0][c], top_grid[1][c], top_grid[2][c], top_grid[3][c]):
            return top_grid[0][c]
    # diagonals
    if four_in_a_row(top_grid[0][0], top_grid[1][1], top_grid[2][2], top_grid[3][3]):
        return top_grid[0][0]
    if four_in_a_row(top_grid[0][3], top_grid[1][2], top_grid[2][1], top_grid[3][0]):
        return top_grid[0][3]

    return None

def is_terminal_state(engine):
    """
    Terminal if there's a winner or no moves left.
    """
    if check_winner(engine.board) is not None:
        return True
    # If no moves => terminal
    moves = engine.generate_moves()
    return (len(moves) == 0)

def hash_state(engine):
    """
    Make a quick string-based hash from the board + supply + current_player.
    Note: For serious performance, consider a Zobrist-based approach.
    """
    rows = len(engine.board)
    cols = len(engine.board[0])
    parts = []
    for r in range(rows):
        for c in range(cols):
            stack = engine.board[r][c]
            # We'll store top to bottom for uniqueness
            stack_str = '-'.join([f"{p['player']}{p['size']}" for p in stack])
            parts.append(stack_str if stack_str else "[]")

    # Supply info
    s1_str = '-'.join([f"{p['size']}({p['used']})" for p in engine.supply1])
    s2_str = '-'.join([f"{p['size']}({p['used']})" for p in engine.supply2])
    parts.append(s1_str)
    parts.append(s2_str)
    parts.append(str(engine.current_player))

    return '|'.join(parts)


####################################################
#               EVALUATION FUNCTION
####################################################

def evaluate(engine):
    """
    A more advanced heuristic:
    1) Big positive if engine.current_player is winning,
       big negative if the opponent is winning.
    2) Evaluate who 'owns' the top of each stack, summing piece-size for top pieces.
    3) Count how many moves current player has vs. opponent (mobility).
    4) Potential lines for each player (like 4-in-a-row opportunities).
    5) Bonus for controlling more squares, especially with bigger pieces.

    Return a numerical value (the bigger, the better for engine.current_player).
    """
    winner = check_winner(engine.board)
    current_player = engine.current_player
    opponent = 1 if current_player == 2 else 2

    # Immediate win check
    if winner == current_player:
        return 1000000
    elif winner == opponent:
        return -1000000

    # Let's gather some stats:
    #  - top control / piece sizes
    #  - mobility
    #  - potential lines
    board = engine.board
    rows = 4
    cols = 4

    # Top-grid: who owns each top
    top_grid = [[0]*cols for _ in range(rows)]
    top_size = [[0]*cols for _ in range(rows)]  # size of top piece
    for r in range(rows):
        for c in range(cols):
            if board[r][c]:
                top_grid[r][c] = board[r][c][0]['player']
                top_size[r][c] = board[r][c][0]['size']
            else:
                top_grid[r][c] = 0
                top_size[r][c] = 0

    # 1. Count total 'top size' for current vs. opponent
    top_size_curr = 0
    top_size_opp = 0
    for r in range(rows):
        for c in range(cols):
            if top_grid[r][c] == current_player:
                top_size_curr += top_size[r][c]
            elif top_grid[r][c] == opponent:
                top_size_opp += top_size[r][c]

    size_factor = top_size_curr - top_size_opp

    # 2. Mobility: number of legal moves for each side
    current_mobility = len(engine.generate_moves())
    # We can simulate flipping the player to see opponent mobility quickly:
    opp_engine = copy.deepcopy(engine)
    opp_engine.current_player = opponent
    opponent_mobility = len(opp_engine.generate_moves())
    mobility_factor = current_mobility - opponent_mobility

    # 3. Potential lines
    lines_for_current = 0
    lines_for_opponent = 0

    all_lines = []
    # rows
    for r in range(rows):
        all_lines.append([(r,0),(r,1),(r,2),(r,3)])
    # columns
    for c in range(cols):
        all_lines.append([(0,c),(1,c),(2,c),(3,c)])
    # diagonals
    all_lines.append([(0,0),(1,1),(2,2),(3,3)])
    all_lines.append([(0,3),(1,2),(2,1),(3,0)])

    #looking at
    for line in all_lines:
        owners = [top_grid[r][c] for (r,c) in line]

        count = 0
        for i in range(len(line)):
            if owners[i] == current_player:
                count += 1
            #the dividing factor divides the score by 2 if the opponents pieces are also on the line
        dividing_factor = 2
        if current_player not in owners:
            dividing_factor = 1
        if count != 0:
            #the score is exponential because the more pieces on a line, the more powerful it is
            lines_for_current += (2**count)//dividing_factor

        #count up all the opponents pieces on winning lines
        count = 0
        for i in range(len(line)):
            if owners[i] == opponent:
                count += 1
            dividing_factor = 2
            if current_player not in owners:
                dividing_factor = 1
            if count != 0:
                lines_for_opponent += (2**count)//dividing_factor

        else:
            continue



    line_factor = lines_for_current - lines_for_opponent

    #diagonal points and center points should have more weight
    prime_spots = []
    prime_spots.append((0,0))
    prime_spots.append((3,0))
    prime_spots.append((0,3))
    prime_spots.append((3,3))
    prime_spots.append((1,1))
    prime_spots.append((2,1))
    prime_spots.append((1,2))
    prime_spots.append((2,2))
    prime_counter_curr = 0
    prime_counter_opponent = 0

    for r in range(rows):
        for c in range(cols):
            if top_grid[r][c] == current_player and prime_spots.__contains__((r,c)):
                prime_counter_curr += 1
            if top_grid[r][c] == opponent and prime_spots.__contains__((r,c)):
                prime_counter_opponent += 1

    prime_spots_factor = prime_counter_curr - prime_counter_opponent


    # Combine factors
    score = (5 * size_factor) + (1 * mobility_factor) + (5 * line_factor) + (2 * prime_spots_factor)

    return score


####################################################
#          MOVE ORDERING (OPTIONAL)
####################################################

def order_moves(moves, engine):
    """
    Sort moves in a way that likely puts more promising moves first:
      - from supply: bigger pieces first
      - from board: bigger piece capturing smaller piece first
    """
    def move_value(m):
        if m['type'] == 'supply':
            # bigger piece has higher priority
            return m['piece']['size']
        else:
            # 'board' move
            r_to, c_to = m['to']
            board_stack = engine.board[r_to][c_to]
            capture_val = 0
            if board_stack:
                top_piece = board_stack[-1]
                # capturing bigger is not possible, but capturing smaller is good
                capture_val = top_piece['size']
            # Also weigh the piece we are moving
            return m['piece']['size'] + capture_val
    moves.sort(key=move_value, reverse=True)
    return moves


####################################################
#          ITERATIVE DEEPENING ALPHA-BETA
####################################################

TRANS_TABLE = {}  # { (state_hash, depth, alpha, beta) : (score, best_move) }

def alpha_beta(engine, depth, alpha, beta, start_time, end_time):
    """
    Standard alpha-beta that returns (best_score, best_move).
    We'll treat 'engine.current_player' as the maximizing side.
    """
    # Time check
    if time.time() >= end_time:
        # Return a static evaluation (no best_move) if out of time
        return evaluate(engine), None

    if depth == 0 or is_terminal_state(engine):
        return evaluate(engine), None

    # Check transposition table
    state_key = (hash_state(engine), depth, alpha, beta)
    if state_key in TRANS_TABLE:
        cached_score, cached_move = TRANS_TABLE[state_key]
        return cached_score, cached_move

    moves = engine.generate_moves()
    if not moves:
        # No moves => evaluate
        score = evaluate(engine)
        TRANS_TABLE[state_key] = (score, None)
        return score, None

    # Move ordering
    moves = order_moves(moves, engine)

    best_score = -float('inf')
    best_move = moves[0]  # default

    for move in moves:
        child = engine.apply_move(move)
        # Recurse with swapped alpha/beta and negative score to keep perspective
        score, _ = alpha_beta(child, depth - 1, -beta, -alpha, start_time, end_time)
        score = -score  # invert

        if score > best_score:
            best_score = score
            best_move = move
        alpha = max(alpha, score)
        if alpha >= beta:
            break

        if time.time() >= end_time:
            break

    TRANS_TABLE[state_key] = (best_score, best_move)
    return best_score, best_move


def iterative_deepening(engine, max_time=20.0):
    """
    Iterative deepening up to ~max_time seconds.
    We'll try depth=1,2,3,... until time is up, caching results.
    """
    global TRANS_TABLE
    TRANS_TABLE.clear()
    start_time = time.time()
    end_time = start_time + max_time

    best_move = None
    best_score = None
    depth = 1

    while True:
        if time.time() >= end_time:
            break

        score, move = alpha_beta(engine, depth, -float('inf'), float('inf'), start_time, end_time)

        # if time's up in the middle of alpha-beta, we'll just break
        if time.time() >= end_time:
            break

        if move is not None:
            best_move = move
            best_score = score

        depth += 1
        # If we found a "winning" move, might as well stop
        if best_score and best_score >= 1000000:
            break

    return best_move, best_score


####################################################
#            MAIN get_move FUNCTION
####################################################

def get_move(engine, max_time=20.0):
    """
    Will think up to `max_time` seconds using iterative deepening alpha-beta.
    Returns the best move found within that time.
    """
    print(f"AI thinking for up to ~{max_time} seconds...")
    move, score = iterative_deepening(engine, max_time=max_time)
    print(f"Chosen move: {move} with score {score}")
    return move


####################################################
#       CREATE ENGINE FROM STATE (if needed)
####################################################

def create_engine_from_state(state):
    """
    Utility to construct the GobbletEngine from a dictionary 'state',
    which must have:
      state['board']
      state['supply1']
      state['supply2']
      state['currentPlayer']
    """
    board = state['board']
    supply1 = state['supply1']
    supply2 = state['supply2']
    current_player = state['currentPlayer']
    return GobbletEngine(board, supply1, supply2, current_player)

####################################################
#               DEMO / TEST
####################################################

if __name__ == '__main__':
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

    engine = GobbletEngine(board, supply1, supply2, current_player=1)

    move = get_move(engine, 5)
    print(move)
    engine = engine.apply_move(move)
    move = get_move(engine, 5)
    print(move)
    engine = engine.apply_move(move)
    move = get_move(engine, 5)
    print(move)
    engine = engine.apply_move(move)
    move = get_move(engine, 5)
    print(move)
    engine = engine.apply_move(move)
    move = get_move(engine, 5)
    print(move)
    engine = engine.apply_move(move)
    move = get_move(engine, 5)
    print(move)
    engine = engine.apply_move(move)
    move = get_move(engine, 5)
    print(move)
    engine = engine.apply_move(move)
    move = get_move(engine, 5)
    print(move)
    engine = engine.apply_move(move)
    move = get_move(engine, 5)
    print(move)
    engine = engine.apply_move(move)

