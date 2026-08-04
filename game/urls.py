from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('api/legal-moves', views.legal_moves, name='legal-moves'),
    path('api/move', views.move_pawn, name='move'),
]
