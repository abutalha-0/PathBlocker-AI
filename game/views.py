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
    serialize_state,
)

SESSION_KEY = 'game_state'


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
    return JsonResponse({
        'state': serialize_state(state),
        'winner': state.players.index(winner) if winner else None,
    })


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
