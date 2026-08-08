from django.test import TestCase

from game.engine import (
    GameState,
    WALL_GRID_SIZE,
    apply_move,
    can_place_wall,
    deserialize_state,
    get_jump_moves,
    get_legal_moves,
    get_legal_wall_placements,
    get_pawn_moves,
    has_path_to_goal,
    is_winner,
    place_wall,
    serialize_state,
    shortest_path_length,
)


class GameStateTests(TestCase):
    def test_new_game_sets_up_standard_start(self):
        state = GameState.new_game()
        self.assertEqual(state.players[0].position, (0, 4))
        self.assertEqual(state.players[0].goal_row, 8)
        self.assertEqual(state.players[1].position, (8, 4))
        self.assertEqual(state.players[1].goal_row, 0)
        self.assertTrue(all(p.walls_left == 10 for p in state.players))
        self.assertEqual(state.turn, 0)
        self.assertIsNone(state.winner)
        self.assertIs(state.current_player, state.players[0])
        self.assertIs(state.opponent, state.players[1])


class SerializationTests(TestCase):
    def test_round_trip_preserves_state(self):
        state = GameState.new_game()
        place_wall(state, 'horizontal', (4, 4), state.players[0])
        state.turn = 1
        state.winner = None

        restored = deserialize_state(serialize_state(state))

        self.assertEqual(restored.turn, state.turn)
        self.assertEqual(restored.winner, state.winner)
        self.assertEqual(restored.horizontal_walls, state.horizontal_walls)
        self.assertEqual(
            [(p.position, p.goal_row, p.walls_left) for p in restored.players],
            [(p.position, p.goal_row, p.walls_left) for p in state.players],
        )

    def test_round_trip_preserves_winner(self):
        state = GameState.new_game()
        state.winner = 1
        restored = deserialize_state(serialize_state(state))
        self.assertEqual(restored.winner, 1)


class PawnMovementTests(TestCase):
    def test_open_start_has_three_moves(self):
        state = GameState.new_game()
        moves = get_pawn_moves(state, state.players[0])
        self.assertCountEqual(moves, [(0, 3), (0, 5), (1, 4)])

    def test_corner_has_only_two_moves(self):
        state = GameState.new_game()
        state.players[0].position = (0, 0)
        moves = get_pawn_moves(state, state.players[0])
        self.assertCountEqual(moves, [(0, 1), (1, 0)])

    def test_wall_blocks_move_in_that_direction(self):
        state = GameState.new_game()
        state.players[0].position = (4, 4)
        state.horizontal_walls.add((4, 4))
        moves = get_pawn_moves(state, state.players[0])
        self.assertNotIn((5, 4), moves)
        self.assertCountEqual(moves, [(3, 4), (4, 3), (4, 5)])

    def test_opponent_occupied_cell_is_not_a_simple_move(self):
        state = GameState.new_game()
        state.players[0].position = (4, 4)
        state.players[1].position = (5, 4)
        moves = get_pawn_moves(state, state.players[0])
        self.assertNotIn((5, 4), moves)


class PawnJumpTests(TestCase):
    def test_straight_jump_over_adjacent_opponent(self):
        state = GameState.new_game()
        state.players[0].position = (4, 4)
        state.players[1].position = (5, 4)
        self.assertEqual(get_jump_moves(state, state.players[0]), [(6, 4)])

    def test_diagonal_jump_when_opponent_at_board_edge(self):
        state = GameState.new_game()
        state.players[0].position = (7, 4)
        state.players[1].position = (8, 4)
        landings = get_jump_moves(state, state.players[0])
        self.assertCountEqual(landings, [(8, 3), (8, 5)])

    def test_diagonal_jump_when_wall_behind_opponent(self):
        state = GameState.new_game()
        state.players[0].position = (4, 4)
        state.players[1].position = (5, 4)
        state.horizontal_walls.add((5, 4))
        landings = get_jump_moves(state, state.players[0])
        self.assertCountEqual(landings, [(5, 3), (5, 5)])

    def test_one_diagonal_blocked_by_wall(self):
        state = GameState.new_game()
        state.players[0].position = (4, 4)
        state.players[1].position = (5, 4)
        state.horizontal_walls.add((5, 4))
        state.vertical_walls.add((4, 4))
        self.assertEqual(get_jump_moves(state, state.players[0]), [(5, 3)])

    def test_no_jump_when_not_adjacent(self):
        state = GameState.new_game()
        self.assertEqual(get_jump_moves(state, state.players[0]), [])

    def test_no_jump_when_wall_between_players(self):
        state = GameState.new_game()
        state.players[0].position = (4, 4)
        state.players[1].position = (5, 4)
        state.horizontal_walls.add((4, 4))
        self.assertEqual(get_jump_moves(state, state.players[0]), [])


class WallPlacementTests(TestCase):
    def test_valid_placement_adds_wall_and_decrements_count(self):
        state = GameState.new_game()
        place_wall(state, 'horizontal', (4, 4), state.players[0])
        self.assertIn((4, 4), state.horizontal_walls)
        self.assertEqual(state.players[0].walls_left, 9)

    def test_duplicate_slot_is_invalid(self):
        state = GameState.new_game()
        place_wall(state, 'horizontal', (4, 4), state.players[0])
        self.assertFalse(can_place_wall(state, 'horizontal', (4, 4), state.players[0]))

    def test_adjacent_overlapping_wall_is_invalid(self):
        state = GameState.new_game()
        place_wall(state, 'horizontal', (4, 4), state.players[0])
        self.assertFalse(can_place_wall(state, 'horizontal', (4, 5), state.players[0]))
        self.assertFalse(can_place_wall(state, 'horizontal', (4, 3), state.players[0]))

    def test_non_overlapping_wall_is_valid(self):
        state = GameState.new_game()
        place_wall(state, 'horizontal', (4, 4), state.players[0])
        self.assertTrue(can_place_wall(state, 'horizontal', (4, 6), state.players[0]))

    def test_crossing_perpendicular_wall_is_invalid(self):
        state = GameState.new_game()
        place_wall(state, 'horizontal', (4, 4), state.players[0])
        self.assertFalse(can_place_wall(state, 'vertical', (4, 4), state.players[0]))

    def test_out_of_range_position_is_invalid(self):
        state = GameState.new_game()
        self.assertFalse(can_place_wall(state, 'horizontal', (8, 4), state.players[0]))
        self.assertFalse(can_place_wall(state, 'horizontal', (-1, 0), state.players[0]))

    def test_no_walls_left_is_invalid(self):
        state = GameState.new_game()
        state.players[0].walls_left = 0
        self.assertFalse(can_place_wall(state, 'horizontal', (2, 2), state.players[0]))

    def test_illegal_placement_raises_and_leaves_state_unchanged(self):
        state = GameState.new_game()
        place_wall(state, 'horizontal', (4, 4), state.players[0])
        with self.assertRaises(ValueError):
            place_wall(state, 'horizontal', (4, 4), state.players[0])


class LegalWallPlacementsTests(TestCase):
    def test_open_board_has_all_slots_in_both_orientations(self):
        state = GameState.new_game()
        placements = get_legal_wall_placements(state, state.players[0])
        self.assertEqual(len(placements), 2 * WALL_GRID_SIZE * WALL_GRID_SIZE)

    def test_no_walls_left_returns_no_placements(self):
        state = GameState.new_game()
        state.players[0].walls_left = 0
        self.assertEqual(get_legal_wall_placements(state, state.players[0]), [])

    def test_placed_wall_removes_overlapping_slots_from_the_list(self):
        state = GameState.new_game()
        place_wall(state, 'horizontal', (4, 4), state.players[0])
        placements = get_legal_wall_placements(state, state.players[0])
        self.assertNotIn(('horizontal', (4, 4)), placements)
        self.assertNotIn(('horizontal', (4, 3)), placements)
        self.assertNotIn(('horizontal', (4, 5)), placements)
        self.assertNotIn(('vertical', (4, 4)), placements)


class WallLegalityTests(TestCase):
    def test_wall_that_leaves_a_path_open_is_valid(self):
        state = GameState.new_game()
        self.assertTrue(can_place_wall(state, 'horizontal', (4, 4), state.players[0]))

    def test_wall_that_would_fully_seal_a_player_is_rejected(self):
        state = GameState.new_game()
        state.players[0].position = (0, 0)
        place_wall(state, 'horizontal', (0, 0), state.players[0])
        self.assertTrue(has_path_to_goal(state, state.players[0]))
        self.assertFalse(can_place_wall(state, 'vertical', (0, 0), state.players[0]))

    def test_rejected_wall_leaves_state_unmutated(self):
        state = GameState.new_game()
        state.players[0].position = (0, 0)
        place_wall(state, 'horizontal', (0, 0), state.players[0])
        can_place_wall(state, 'vertical', (0, 0), state.players[0])
        self.assertEqual(state.vertical_walls, set())

    def test_fully_boxed_corner_has_no_path(self):
        state = GameState.new_game()
        state.players[0].position = (0, 0)
        state.horizontal_walls.add((0, 0))
        state.vertical_walls.add((0, 1))
        self.assertFalse(has_path_to_goal(state, state.players[0]))

    def test_detour_around_separated_walls_still_has_path(self):
        state = GameState.new_game()
        state.players[0].position = (4, 4)
        place_wall(state, 'horizontal', (4, 2), state.players[0])
        place_wall(state, 'horizontal', (4, 4), state.players[0])
        place_wall(state, 'horizontal', (4, 6), state.players[0])
        self.assertTrue(has_path_to_goal(state, state.players[0]))


class ShortestPathTests(TestCase):
    def test_distance_on_open_board_is_straight_line(self):
        state = GameState.new_game()
        self.assertEqual(shortest_path_length(state, state.players[0]), 8)
        self.assertEqual(shortest_path_length(state, state.players[1]), 8)

    def test_zero_distance_when_already_on_goal_row(self):
        state = GameState.new_game()
        state.players[0].position = (8, 0)
        self.assertEqual(shortest_path_length(state, state.players[0]), 0)

    def test_wall_detour_increases_distance(self):
        state = GameState.new_game()
        place_wall(state, 'horizontal', (4, 2), state.players[0])
        place_wall(state, 'horizontal', (4, 4), state.players[0])
        place_wall(state, 'horizontal', (4, 6), state.players[0])
        self.assertGreater(shortest_path_length(state, state.players[0]), 8)

    def test_unreachable_goal_returns_none(self):
        state = GameState.new_game()
        state.players[0].position = (0, 0)
        state.horizontal_walls.add((0, 0))
        state.vertical_walls.add((0, 1))
        self.assertIsNone(shortest_path_length(state, state.players[0]))


class GetLegalMovesTests(TestCase):
    def test_open_board_combines_pawn_and_wall_moves(self):
        state = GameState.new_game()
        moves = get_legal_moves(state, state.players[0])
        pawn_moves = [m for m in moves if m[0] == 'move']
        wall_moves = [m for m in moves if m[0] == 'wall']
        self.assertCountEqual(pawn_moves, [('move', (0, 3)), ('move', (0, 5)), ('move', (1, 4))])
        self.assertEqual(len(wall_moves), 2 * WALL_GRID_SIZE * WALL_GRID_SIZE)

    def test_no_walls_left_returns_only_pawn_moves(self):
        state = GameState.new_game()
        state.players[0].walls_left = 0
        moves = get_legal_moves(state, state.players[0])
        self.assertTrue(all(m[0] == 'move' for m in moves))

    def test_every_move_is_accepted_by_apply_move(self):
        state = GameState.new_game()
        for move in get_legal_moves(state, state.players[0]):
            trial = GameState.new_game()
            apply_move(trial, move)


class ApplyMoveTests(TestCase):
    def test_legal_move_updates_position_and_switches_turn(self):
        state = GameState.new_game()
        winner = apply_move(state, ('move', (1, 4)))
        self.assertEqual(state.players[0].position, (1, 4))
        self.assertEqual(state.turn, 1)
        self.assertIsNone(winner)

    def test_illegal_move_raises_and_leaves_turn_unchanged(self):
        state = GameState.new_game()
        with self.assertRaises(ValueError):
            apply_move(state, ('move', (5, 5)))
        self.assertEqual(state.turn, 0)

    def test_wall_move_type_places_wall_and_switches_turn(self):
        state = GameState.new_game()
        apply_move(state, ('wall', 'horizontal', (4, 4)))
        self.assertIn((4, 4), state.horizontal_walls)
        self.assertEqual(state.players[0].walls_left, 9)
        self.assertEqual(state.turn, 1)

    def test_illegal_wall_move_raises(self):
        state = GameState.new_game()
        apply_move(state, ('wall', 'horizontal', (4, 4)))
        state.turn = 0
        with self.assertRaises(ValueError):
            apply_move(state, ('wall', 'horizontal', (4, 4)))

    def test_win_detected_when_reaching_goal_row(self):
        state = GameState.new_game()
        state.players[0].position = (7, 4)
        state.players[1].position = (8, 8)
        winner = apply_move(state, ('move', (8, 4)))
        self.assertEqual(winner, 0)
        self.assertEqual(state.winner, 0)
        self.assertTrue(is_winner(state.players[0]))

    def test_no_moves_allowed_after_game_is_won(self):
        state = GameState.new_game()
        state.players[0].position = (7, 4)
        state.players[1].position = (8, 8)
        apply_move(state, ('move', (8, 4)))
        with self.assertRaises(ValueError):
            apply_move(state, ('move', (7, 8)))

    def test_turn_alternates_across_moves(self):
        state = GameState.new_game()
        turns = [state.turn]
        apply_move(state, ('move', (1, 4)))
        turns.append(state.turn)
        apply_move(state, ('move', (7, 4)))
        turns.append(state.turn)
        self.assertEqual(turns, [0, 1, 0])

    def test_unknown_move_type_raises(self):
        state = GameState.new_game()
        with self.assertRaises(ValueError):
            apply_move(state, ('teleport', (0, 0)))
