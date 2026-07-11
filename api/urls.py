from django.urls import path
from . import views

urlpatterns = [
    # Când cineva accesează linkul '/predict/', Django va rula funcția get_prediction
    path('predict/', views.get_prediction, name='predict'),
]