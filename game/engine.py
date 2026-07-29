from dataclasses import dataclass, field

BOARD_SIZE = 9
WALLS_PER_PLAYER = 10

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
    # Each wall entry (row, col) marks the intersection it's anchored to,
    # 0..7 on both axes; a wall spans two cell-edges from that intersection.
    players: list[Player]
    turn: int = 0
    horizontal_walls: set[tuple[int, int]] = field(default_factory=set)
    vertical_walls: set[tuple[int, int]] = field(default_factory=set)

    @classmethod
    def new_game(cls):
        player_one = Player(position=(0, 4), goal_row=BOARD_SIZE - 1)
        player_two = Player(position=(BOARD_SIZE - 1, 4), goal_row=0)
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
