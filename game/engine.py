import copy
import time
from collections import deque
from dataclasses import dataclass, field

BOARD_SIZE = 9
WALLS_PER_PLAYER = 10
WALL_GRID_SIZE = BOARD_SIZE - 1

DIRECTIONS = {
    'up': (-1, 0),
    'down': (1, 0),
    'left': (0, -1),
    'right': (0, 1),
}

PERPENDICULARS = {
    'up': ('left', 'right'),
    'down': ('left', 'right'),
    'left': ('up', 'down'),
    'right': ('up', 'down'),
}


@dataclass
class Player:
    position: tuple[int, int]
    goal_row: int
    walls_left: int = WALLS_PER_PLAYER


@dataclass
class GameState:
    # Each wall key (row, col) marks the intersection it's anchored to,
    # 0..7 on both axes; a wall spans two cell-edges from that intersection.
    # The value is the index of the player who placed it.
    players: list[Player]
    turn: int = 0
    horizontal_walls: dict[tuple[int, int], int] = field(default_factory=dict)
    vertical_walls: dict[tuple[int, int], int] = field(default_factory=dict)
    winner: int | None = None

    @classmethod
    def new_game(cls):
        # Player one (human, moves first) starts at the bottom edge and
        # aims for the top row; player two (AI) starts at the top and
        # aims for the bottom.
        player_one = Player(position=(BOARD_SIZE - 1, 4), goal_row=0)
        player_two = Player(position=(0, 4), goal_row=BOARD_SIZE - 1)
        return cls(players=[player_one, player_two])

    @property
    def current_player(self):
        return self.players[self.turn]

    @property
    def opponent(self):
        return self.players[1 - self.turn]


def in_bounds(position):
    row, col = position
    return 0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE


def is_wall_blocking(state, position, direction):
    row, col = position
    if direction == 'down':
        return (row, col) in state.horizontal_walls or (row, col - 1) in state.horizontal_walls
    if direction == 'up':
        return (row - 1, col) in state.horizontal_walls or (row - 1, col - 1) in state.horizontal_walls
    if direction == 'right':
        return (row, col) in state.vertical_walls or (row - 1, col) in state.vertical_walls
    if direction == 'left':
        return (row, col - 1) in state.vertical_walls or (row - 1, col - 1) in state.vertical_walls
    raise ValueError(f'unknown direction: {direction}')


def get_pawn_moves(state, player=None):
    player = player or state.current_player
    occupied = {p.position for p in state.players if p is not player}

    moves = []
    for direction, (dr, dc) in DIRECTIONS.items():
        row, col = player.position
        target = (row + dr, col + dc)
        if not in_bounds(target):
            continue
        if is_wall_blocking(state, player.position, direction):
            continue
        if target in occupied:
            continue
        moves.append(target)
    return moves


def get_jump_moves(state, player=None):
    player = player or state.current_player
    opponent = next(p for p in state.players if p is not player)

    direction = None
    for candidate, (dr, dc) in DIRECTIONS.items():
        row, col = player.position
        if (row + dr, col + dc) == opponent.position and not is_wall_blocking(state, player.position, candidate):
            direction = candidate
            break
    if direction is None:
        return []

    dr, dc = DIRECTIONS[direction]
    orow, ocol = opponent.position
    straight_landing = (orow + dr, ocol + dc)
    if in_bounds(straight_landing) and not is_wall_blocking(state, opponent.position, direction):
        return [straight_landing]

    landings = []
    for side in PERPENDICULARS[direction]:
        sdr, sdc = DIRECTIONS[side]
        landing = (orow + sdr, ocol + sdc)
        if in_bounds(landing) and not is_wall_blocking(state, opponent.position, side):
            landings.append(landing)
    return landings


def shortest_path_cells(state, player):
    start = player.position
    if start[0] == player.goal_row:
        return [start]

    parents = {start: None}
    queue = deque([start])
    while queue:
        row, col = queue.popleft()
        for direction, (dr, dc) in DIRECTIONS.items():
            neighbor = (row + dr, col + dc)
            if neighbor in parents or not in_bounds(neighbor):
                continue
            if is_wall_blocking(state, (row, col), direction):
                continue
            parents[neighbor] = (row, col)
            if neighbor[0] == player.goal_row:
                path = [neighbor]
                while parents[path[-1]] is not None:
                    path.append(parents[path[-1]])
                path.reverse()
                return path
            queue.append(neighbor)
    return None


def shortest_path_length(state, player):
    path = shortest_path_cells(state, player)
    return None if path is None else len(path) - 1


def has_path_to_goal(state, player):
    return shortest_path_length(state, player) is not None


def can_place_wall(state, orientation, position, player=None):
    player = player or state.current_player
    if player.walls_left <= 0:
        return False

    row, col = position
    if not (0 <= row < WALL_GRID_SIZE and 0 <= col < WALL_GRID_SIZE):
        return False

    if orientation == 'horizontal':
        walls, crossing = state.horizontal_walls, state.vertical_walls
        if (row, col) in walls or (row, col - 1) in walls or (row, col + 1) in walls:
            return False
    elif orientation == 'vertical':
        walls, crossing = state.vertical_walls, state.horizontal_walls
        if (row, col) in walls or (row - 1, col) in walls or (row + 1, col) in walls:
            return False
    else:
        raise ValueError(f'unknown orientation: {orientation}')

    if (row, col) in crossing:
        return False

    walls[position] = -1  # placeholder owner; only legality matters here
    try:
        return all(has_path_to_goal(state, p) for p in state.players)
    finally:
        del walls[position]


def place_wall(state, orientation, position, player=None):
    player = player or state.current_player
    if not can_place_wall(state, orientation, position, player):
        raise ValueError(f'illegal wall placement: {orientation} at {position}')

    walls = state.horizontal_walls if orientation == 'horizontal' else state.vertical_walls
    walls[position] = state.players.index(player)
    player.walls_left -= 1


def get_legal_wall_placements(state, player=None):
    player = player or state.current_player
    if player.walls_left <= 0:
        return []

    placements = []
    for orientation in ('horizontal', 'vertical'):
        for row in range(WALL_GRID_SIZE):
            for col in range(WALL_GRID_SIZE):
                if can_place_wall(state, orientation, (row, col), player):
                    placements.append((orientation, (row, col)))
    return placements


def get_legal_pawn_targets(state, player=None):
    player = player or state.current_player
    return set(get_pawn_moves(state, player)) | set(get_jump_moves(state, player))


def _cells_touching_wall(row, col):
    return {(row, col), (row, col + 1), (row + 1, col), (row + 1, col + 1)}


def get_near_path_wall_candidates(state, player=None):
    """Wall placements touching either player's current shortest path.

    A full search of all wall slots dominates the branching factor and
    makes deep search too slow; walls far from both paths are almost
    never worth playing, so search only considers these candidates.
    """
    player = player or state.current_player
    if player.walls_left <= 0:
        return []

    opponent = next(p for p in state.players if p is not player)
    path_cells = set(shortest_path_cells(state, player) or [])
    path_cells |= set(shortest_path_cells(state, opponent) or [])

    candidates = []
    for orientation in ('horizontal', 'vertical'):
        for row in range(WALL_GRID_SIZE):
            for col in range(WALL_GRID_SIZE):
                if not _cells_touching_wall(row, col) & path_cells:
                    continue
                if can_place_wall(state, orientation, (row, col), player):
                    candidates.append((orientation, (row, col)))
    return candidates


def get_legal_moves(state, player=None):
    player = player or state.current_player
    opponent = next(p for p in state.players if p is not player)

    pawn_moves = sorted(
        (('move', target) for target in get_legal_pawn_targets(state, player)),
        key=lambda move: abs(move[1][0] - player.goal_row),
    )
    wall_moves = sorted(
        (
            ('wall', orientation, position)
            for orientation, position in get_near_path_wall_candidates(state, player)
        ),
        key=lambda move: abs(move[2][0] - opponent.position[0]) + abs(move[2][1] - opponent.position[1]),
    )
    return pawn_moves + wall_moves


def is_winner(player):
    return player.position[0] == player.goal_row


def apply_move(state, move):
    if state.winner is not None:
        raise ValueError('game is already over')

    player_index = state.turn
    player = state.players[player_index]
    kind = move[0]

    if kind == 'move':
        _, target = move
        if target not in get_legal_pawn_targets(state, player):
            raise ValueError(f'illegal pawn move: {target}')
        player.position = target
    elif kind == 'wall':
        _, orientation, position = move
        place_wall(state, orientation, position, player)
    else:
        raise ValueError(f'unknown move type: {kind}')

    if is_winner(player):
        state.winner = player_index

    state.turn = 1 - state.turn
    return state.winner


WIN_SCORE = 1000

# Without a cost for spending walls, the search treats every wall's
# path-distance swing as pure profit and over-uses them relative to
# just advancing; this makes spending one a deliberate trade-off.
WALL_CONSERVATION_WEIGHT = 3


def evaluate(state, player_index):
    if state.winner is not None:
        return WIN_SCORE if state.winner == player_index else -WIN_SCORE

    player = state.players[player_index]
    opponent = state.players[1 - player_index]
    distance_term = shortest_path_length(state, opponent) - shortest_path_length(state, player)
    wall_term = player.walls_left - opponent.walls_left
    return distance_term + WALL_CONSERVATION_WEIGHT * wall_term


def minimax(state, depth, maximizing_index):
    if depth == 0 or state.winner is not None:
        return evaluate(state, maximizing_index), None

    is_maximizing = state.turn == maximizing_index
    best_move = None
    best_score = float('-inf') if is_maximizing else float('inf')

    for move in get_legal_moves(state):
        child = copy.deepcopy(state)
        apply_move(child, move)
        score, _ = minimax(child, depth - 1, maximizing_index)

        if is_maximizing and score > best_score:
            best_score, best_move = score, move
        elif not is_maximizing and score < best_score:
            best_score, best_move = score, move

    return best_score, best_move


def minimax_alpha_beta(state, depth, maximizing_index, alpha=float('-inf'), beta=float('inf')):
    if depth == 0 or state.winner is not None:
        return evaluate(state, maximizing_index), None

    is_maximizing = state.turn == maximizing_index
    best_move = None
    best_score = float('-inf') if is_maximizing else float('inf')

    for move in get_legal_moves(state):
        child = copy.deepcopy(state)
        apply_move(child, move)
        score, _ = minimax_alpha_beta(child, depth - 1, maximizing_index, alpha, beta)

        if is_maximizing:
            if score > best_score:
                best_score, best_move = score, move
            alpha = max(alpha, best_score)
        else:
            if score < best_score:
                best_score, best_move = score, move
            beta = min(beta, best_score)

        if beta <= alpha:
            break

    return best_score, best_move


def choose_greedy_move(state, player_index):
    """Pick whichever legal pawn move most reduces the player's own
    path distance. No lookahead and never places a wall — this is the
    Easy tier, deliberately weaker than the minimax-based tiers.
    """
    player = state.players[player_index]
    best_move = None
    best_distance = None

    for target in get_legal_pawn_targets(state, player):
        child = copy.deepcopy(state)
        child.players[player_index].position = target
        distance = shortest_path_length(child, child.players[player_index])
        if best_distance is None or (distance is not None and distance < best_distance):
            best_distance = distance
            best_move = ('move', target)

    return best_move


def choose_minimax_move(state, maximizing_index, max_depth, time_budget):
    """Iterative deepening: search depth 1, 2, ... up to max_depth,
    keeping the best move found so far, stopping once time_budget is
    spent so a response is always returned promptly.
    """
    start = time.monotonic()
    best_move = None

    for depth in range(1, max_depth + 1):
        if time.monotonic() - start >= time_budget:
            break
        _, move = minimax_alpha_beta(state, depth, maximizing_index)
        if move is not None:
            best_move = move
        if time.monotonic() - start >= time_budget:
            break

    return best_move


DIFFICULTY_LEVELS = {
    'easy': {'strategy': 'greedy'},
    'medium': {'strategy': 'minimax', 'max_depth': 2, 'time_budget': 1.0},
    'hard': {'strategy': 'minimax', 'max_depth': 3, 'time_budget': 2.0},
}


def choose_ai_move(state, player_index, difficulty='medium'):
    settings = DIFFICULTY_LEVELS[difficulty]
    if settings['strategy'] == 'greedy':
        return choose_greedy_move(state, player_index)
    return choose_minimax_move(state, player_index, settings['max_depth'], settings['time_budget'])


def serialize_state(state):
    return {
        'board_size': BOARD_SIZE,
        'turn': state.turn,
        'winner': state.winner,
        'players': [
            {
                'position': list(p.position),
                'goal_row': p.goal_row,
                'walls_left': p.walls_left,
            }
            for p in state.players
        ],
        'horizontal_walls': [[row, col, owner] for (row, col), owner in state.horizontal_walls.items()],
        'vertical_walls': [[row, col, owner] for (row, col), owner in state.vertical_walls.items()],
    }


def deserialize_state(data):
    players = [
        Player(
            position=tuple(p['position']),
            goal_row=p['goal_row'],
            walls_left=p['walls_left'],
        )
        for p in data['players']
    ]
    return GameState(
        players=players,
        turn=data['turn'],
        horizontal_walls={(row, col): owner for row, col, owner in data['horizontal_walls']},
        vertical_walls={(row, col): owner for row, col, owner in data['vertical_walls']},
        winner=data.get('winner'),
    )
