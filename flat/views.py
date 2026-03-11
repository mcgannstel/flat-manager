from decimal import Decimal

from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Sum, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import TransactionForm
from .models import Transaction, RosterAssignment


def is_staff_user(user):
    return user.is_staff or user.is_superuser


@login_required
def dashboard(request):
    transactions = Transaction.objects.select_related(
        "created_by", "paid_by", "reimbursed_to"
    ).order_by("-date", "-created_at")[:10]

    total_in = (
        Transaction.objects.filter(transaction_type="IN")
        .aggregate(total=Sum("amount"))["total"]
        or Decimal("0.00")
    )

    # Only money actually paid out of the flat account/card reduces flat balance
    total_out = (
        Transaction.objects.filter(
            transaction_type="OUT",
            payment_source="FLAT",
        ).aggregate(total=Sum("amount"))["total"]
        or Decimal("0.00")
    )

    balance = total_in - total_out

    pending_claims = Transaction.objects.select_related(
        "created_by", "paid_by", "reimbursed_to"
    ).filter(
        is_claim=True,
        claim_status="PENDING",
    ).order_by("-date", "-created_at")

    pending_claim_total = (
        pending_claims.aggregate(total=Sum("amount"))["total"]
        or Decimal("0.00")
    )

    today = timezone.localdate()
    this_week_start = today - timezone.timedelta(days=today.weekday())

    my_chore = (
        RosterAssignment.objects.select_related("chore", "user")
        .filter(user=request.user, week_start=this_week_start)
        .first()
    )

    weekly_roster = (
        RosterAssignment.objects.select_related("chore", "user")
        .filter(week_start=this_week_start)
        .order_by("chore__name", "user__username")
    )

    context = {
        "transactions": transactions,
        "total_in": total_in,
        "total_out": total_out,
        "balance": balance,
        "pending_claims": pending_claims,
        "pending_claim_total": pending_claim_total,
        "my_chore": my_chore,
        "weekly_roster": weekly_roster,
        "this_week_start": this_week_start,
    }
    return render(request, "flat/dashboard.html", context)


@login_required
def transaction_list(request):
    transactions = Transaction.objects.select_related(
        "created_by", "paid_by", "reimbursed_to"
    ).order_by("-date", "-created_at")

    context = {
        "transactions": transactions,
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
            return redirect("transaction_list")
    else:
        form = TransactionForm()

    context = {
        "form": form,
    }
    return render(request, "flat/add_transaction.html", context)


@login_required
def my_claims(request):
    claims = Transaction.objects.select_related(
        "created_by", "paid_by", "reimbursed_to"
    ).filter(
        is_claim=True
    ).filter(
        Q(reimbursed_to=request.user) | Q(paid_by=request.user)
    ).order_by("-date", "-created_at")

    context = {
        "claims": claims,
    }
    return render(request, "flat/my_claims.html", context)


@login_required
@user_passes_test(is_staff_user)
def mark_claim_paid(request, transaction_id):
    claim = get_object_or_404(
        Transaction,
        id=transaction_id,
        is_claim=True,
        claim_status="PENDING",
    )

    claim.claim_status = "PAID"
    claim.reimbursed_date = timezone.localdate()
    claim.save()

    # Create the actual flat-account reimbursement transaction
    Transaction.objects.create(
        date=timezone.localdate(),
        description=f"Reimbursement for: {claim.description}",
        category="Reimbursement",
        amount=claim.amount,
        transaction_type="OUT",
        payment_source="FLAT",
        created_by=request.user,
        paid_by=claim.reimbursed_to,
        notes=f"Auto-created when claim #{claim.id} was marked paid.",
    )

    return redirect("dashboard")