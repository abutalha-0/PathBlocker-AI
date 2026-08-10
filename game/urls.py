from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('api/legal-moves', views.legal_moves, name='legal-moves'),
    path('api/move', views.move_pawn, name='move'),
    path('api/wall', views.place_wall, name='wall'),
    path('api/ai-move', views.ai_move, name='ai-move'),
    path('api/new-game', views.new_game, name='new-game'),
]
