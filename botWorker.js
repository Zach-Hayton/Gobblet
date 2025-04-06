// botWorker.js

// Listen for messages from the main thread
self.onmessage = function(e) {
  const { state, timeLimit } = e.data;
  // Set a deadline (timestamp)
  const deadline = Date.now() + timeLimit;
  let bestMove = null;
  let depth = 1;
  
  // Iterative deepening loop
  while (Date.now() < deadline) {
    const result = minimax(state, depth, -Infinity, Infinity, true, deadline);
    if (result && result.move) {
      bestMove = result.move;
    }
    depth++;
    // Break if we reached a terminal win/loss evaluation
    if (Math.abs(result.score) === Infinity) break;
  }
  
  // Return the best move found
  self.postMessage({ move: bestMove });
};

// A very simplified evaluation function
function evaluate(state, player) {
  // For now, we simply return 0.
  // A real evaluation would count potential winning lines, etc.
  return 0;
}

// Clone state (shallow clone may suffice for our arrays)
function cloneState(state) {
  return {
    board: state.board.map(row => row.map(cell => cell.slice())),
    supply1: state.supply1.map(piece => Object.assign({}, piece)),
    supply2: state.supply2.map(piece => Object.assign({}, piece)),
    currentPlayer: state.currentPlayer
  };
}

// Generate legal moves for the current player
function generateMoves(state) {
  const moves = [];
  const player = state.currentPlayer;
  // Moves from supply:
  const supply = player === 1 ? state.supply1 : state.supply2;
  supply.forEach(piece => {
    if (!piece.used) {
      // Try placing this piece on every board square if legal
      for (let r = 0; r < state.board.length; r++) {
        for (let c = 0; c < state.board[0].length; c++) {
          const stack = state.board[r][c];
          if (stack.length === 0 || piece.size > stack[stack.length - 1].size) {
            moves.push({
              type: "supply",
              piece: piece,
              to: { row: r, col: c }
            });
          }
        }
      }
    }
  });
  // Moves from board: pick up your own top piece and place it somewhere else
  for (let r = 0; r < state.board.length; r++) {
    for (let c = 0; c < state.board[0].length; c++) {
      const stack = state.board[r][c];
      if (stack.length > 0 && stack[stack.length - 1].player === player) {
        const piece = stack[stack.length - 1];
        // Remove piece temporarily and try placing it elsewhere
        for (let r2 = 0; r2 < state.board.length; r2++) {
          for (let c2 = 0; c2 < state.board[0].length; c2++) {
            if (r === r2 && c === c2) continue;
            const destStack = state.board[r2][c2];
            if (destStack.length === 0 || piece.size > destStack[destStack.length - 1].size) {
              moves.push({
                type: "board",
                piece: piece,
                from: { row: r, col: c },
                to: { row: r2, col: c2 }
              });
            }
          }
        }
      }
    }
  }
  return moves;
}

// Minimax algorithm with alpha-beta pruning and deadline check
function minimax(state, depth, alpha, beta, maximizingPlayer, deadline) {
  if (Date.now() > deadline) {
    return { score: 0 }; // time's up, return neutral
  }
  
  const moves = generateMoves(state);
  // Terminal state: if no moves, evaluate state
  if (depth === 0 || moves.length === 0) {
    const score = evaluate(state, state.currentPlayer);
    return { score: score };
  }
  
  let bestMove = null;
  
  if (maximizingPlayer) {
    let maxEval = -Infinity;
    for (const move of moves) {
      const newState = applyMove(cloneState(state), move);
      newState.currentPlayer = newState.currentPlayer === 1 ? 2 : 1;
      const evalResult = minimax(newState, depth - 1, alpha, beta, false, deadline);
      if (evalResult.score > maxEval) {
        maxEval = evalResult.score;
        bestMove = move;
      }
      alpha = Math.max(alpha, evalResult.score);
      if (beta <= alpha) break;
      if (Date.now() > deadline) break;
    }
    return { score: maxEval, move: bestMove };
  } else {
    let minEval = Infinity;
    for (const move of moves) {
      const newState = applyMove(cloneState(state), move);
      newState.currentPlayer = newState.currentPlayer === 1 ? 2 : 1;
      const evalResult = minimax(newState, depth - 1, alpha, beta, true, deadline);
      if (evalResult.score < minEval) {
        minEval = evalResult.score;
        bestMove = move;
      }
      beta = Math.min(beta, evalResult.score);
      if (beta <= alpha) break;
      if (Date.now() > deadline) break;
    }
    return { score: minEval, move: bestMove };
  }
}

// Apply a move to a state copy (returns modified state)
function applyMove(state, move) {
  if (move.type === "supply") {
    // Mark piece as used in supply
    const supply = move.piece.player === 1 ? state.supply1 : state.supply2;
    const p = supply.find(p => p.id === move.piece.id);
    if (p) p.used = true;
  } else if (move.type === "board") {
    // Remove piece from original square
    const fromStack = state.board[move.from.row][move.from.col];
    if (fromStack.length > 0) fromStack.pop();
  }
  // Place piece on destination square
  state.board[move.to.row][move.to.col].push({
    player: move.piece.player,
    size: move.piece.size,
    id: move.piece.id
  });
  return state;
}
