from dataclasses import dataclass, field

BOARD_SIZE = 9
WALLS_PER_PLAYER = 10

DIRECTIONS = {
    'up': (-1, 0),
    'down': (1, 0),
    'left': (0, -1),
    'right': (0, 1),
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
