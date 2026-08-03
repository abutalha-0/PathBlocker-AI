from django.shortcuts import render

from game.engine import GameState, serialize_state


def index(request):
    state = GameState.new_game()
    return render(request, 'game/index.html', {'state': serialize_state(state)})
