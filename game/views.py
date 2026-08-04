import json

from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET, require_POST

from game.engine import (
    GameState,
    apply_move,
    deserialize_state,
    get_legal_pawn_targets,
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


def index(request):
    state = _load_state(request)
    _save_state(request, state)
    return render(request, 'game/index.html', {'state': serialize_state(state)})


@require_GET
def legal_moves(request):
    state = _load_state(request)
    targets = get_legal_pawn_targets(state, state.current_player)
    return JsonResponse({'targets': [list(t) for t in targets]})


@require_POST
def move_pawn(request):
    state = _load_state(request)
    payload = json.loads(request.body)
    target = tuple(payload['target'])

    try:
        winner = apply_move(state, ('move', target))
    except ValueError as exc:
        return JsonResponse({'error': str(exc)}, status=400)

    _save_state(request, state)
    return JsonResponse({
        'state': serialize_state(state),
        'winner': state.players.index(winner) if winner else None,
    })
