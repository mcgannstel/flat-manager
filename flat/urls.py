from django.urls import path
from . import views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("transactions/", views.transaction_list, name="transaction_list"),
    path("transactions/add/", views.add_transaction, name="add_transaction"),
    path("claims/", views.my_claims, name="my_claims"),
    path("claims/<int:transaction_id>/paid/", views.mark_claim_paid, name="mark_claim_paid"),
]