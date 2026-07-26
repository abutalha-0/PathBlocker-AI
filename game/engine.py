from dataclasses import dataclass, field

BOARD_SIZE = 9
WALLS_PER_PLAYER = 10


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
