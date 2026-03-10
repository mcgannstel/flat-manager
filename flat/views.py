from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Sum, Case, When, DecimalField
from django.db.models.functions import Coalesce
from django.contrib import messages
from django.utils import timezone

from .models import Transaction
from .forms import TransactionForm


@login_required
def dashboard(request):
    transactions = Transaction.objects.order_by("-date", "-id")[:10]

    total_in = Transaction.objects.filter(transaction_type="IN").aggregate(
        total=Coalesce(Sum("amount"), 0, output_field=DecimalField(max_digits=10, decimal_places=2))
    )["total"]

    total_out = Transaction.objects.filter(transaction_type="OUT").aggregate(
        total=Coalesce(Sum("amount"), 0, output_field=DecimalField(max_digits=10, decimal_places=2))
    )["total"]

    pending_claims = Transaction.objects.filter(
        is_claim=True,
        claim_status="PENDING"
    ).order_by("date")

    pending_claim_total = pending_claims.aggregate(
        total=Coalesce(Sum("amount"), 0, output_field=DecimalField(max_digits=10, decimal_places=2))
    )["total"]

    balance = total_in - total_out

    context = {
        "transactions": transactions,
        "total_in": total_in,
        "total_out": total_out,
        "balance": balance,
        "pending_claims": pending_claims,
        "pending_claim_total": pending_claim_total,
    }
    return render(request, "flat/dashboard.html", context)


@login_required
def transaction_list(request):
    transactions = Transaction.objects.order_by("-date", "-id")

    total_in = Transaction.objects.filter(transaction_type="IN").aggregate(
        total=Coalesce(Sum("amount"), 0, output_field=DecimalField(max_digits=10, decimal_places=2))
    )["total"]

    total_out = Transaction.objects.filter(transaction_type="OUT").aggregate(
        total=Coalesce(Sum("amount"), 0, output_field=DecimalField(max_digits=10, decimal_places=2))
    )["total"]

    balance = total_in - total_out

    context = {
        "transactions": transactions,
        "total_in": total_in,
        "total_out": total_out,
        "balance": balance,
    }
    return render(request, "flat/transaction_list.html", context)


@login_required
def add_transaction(request):
    if request.method == "POST":
        form = TransactionForm(request.POST)
        if form.is_valid():
            transaction = form.save(commit=False)
            transaction.created_by = request.user
            transaction.save()
            messages.success(request, "Transaction added successfully.")
            return redirect("transaction_list")
    else:
        form = TransactionForm()

    return render(request, "flat/add_transaction.html", {"form": form})


def is_admin_user(user):
    return user.is_superuser or user.is_staff


@user_passes_test(is_admin_user)
def mark_claim_paid(request, transaction_id):
    transaction = get_object_or_404(Transaction, id=transaction_id, is_claim=True)

    transaction.claim_status = "PAID"
    transaction.reimbursed_date = timezone.localdate()
    transaction.save()

    messages.success(request, "Claim marked as paid.")
    return redirect("transaction_list")