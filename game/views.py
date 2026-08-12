import json

from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET, require_POST

from game.engine import (
    GameState,
    apply_move,
    deserialize_state,
    get_legal_pawn_targets,
    get_legal_wall_placements,
    minimax_alpha_beta,
    serialize_state,
)

SESSION_KEY = 'game_state'

# Move ordering plus restricted wall candidates keep depth 2 under
# ~0.2s; difficulty tiers with their own depth/time budget come later.
AI_SEARCH_DEPTH = 2


def _load_state(request):
    data = request.session.get(SESSION_KEY)
    if data is None:
        return GameState.new_game()
    return deserialize_state(data)


def _save_state(request, state):
    request.session[SESSION_KEY] = serialize_state(state)


def _apply_and_respond(request, state, move):
    try:
        winner = apply_move(state, move)
    except ValueError as exc:
        return JsonResponse({'error': str(exc)}, status=400)

    _save_state(request, state)
    return JsonResponse({'state': serialize_state(state), 'winner': winner})


def index(request):
    state = _load_state(request)
    _save_state(request, state)
    return render(request, 'game/index.html', {'state': serialize_state(state)})


@require_GET
def legal_moves(request):
    state = _load_state(request)
    player = state.current_player
    targets = get_legal_pawn_targets(state, player)
    walls = get_legal_wall_placements(state, player)
    return JsonResponse({
        'targets': [list(t) for t in targets],
        'walls': [[orientation, list(position)] for orientation, position in walls],
    })


@require_POST
def move_pawn(request):
    state = _load_state(request)
    payload = json.loads(request.body)
    target = tuple(payload['target'])
    return _apply_and_respond(request, state, ('move', target))


@require_POST
def place_wall(request):
    state = _load_state(request)
    payload = json.loads(request.body)
    orientation = payload['orientation']
    position = tuple(payload['position'])
    return _apply_and_respond(request, state, ('wall', orientation, position))


@require_POST
def ai_move(request):
    state = _load_state(request)
    _, move = minimax_alpha_beta(state, depth=AI_SEARCH_DEPTH, maximizing_index=state.turn)
    if move is None:
        return JsonResponse({'error': 'no legal moves available'}, status=400)
    return _apply_and_respond(request, state, move)


@require_POST
def new_game(request):
    state = GameState.new_game()
    _save_state(request, state)
    return JsonResponse({'state': serialize_state(state)})
