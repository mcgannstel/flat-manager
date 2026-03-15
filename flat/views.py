from decimal import Decimal
from datetime import datetime, timedelta
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Sum, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils import timezone
from django.utils.dateparse import parse_date
from .forms import TransactionForm
from .models import Transaction, RosterAssignment
from .forms import ReceiveRentForm
from .models import Transaction
from decimal import Decimal
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.shortcuts import redirect, render
from .forms import ReceiveRentForm
from .models import Transaction
User = get_user_model()

def is_staff_user(user):
    return user.is_staff or user.is_superuser


@login_required
def dashboard(request):
    today = timezone.localdate()
    this_week_start = today - timezone.timedelta(days=today.weekday())
    transactions = Transaction.objects.select_related(
        "created_by", "paid_by", "reimbursed_to"
    ).exclude(category="Reimbursement").order_by("-date", "-created_at")[:10]

    total_in = (
        Transaction.objects.filter(transaction_type="IN")
        .aggregate(total=Sum("amount"))["total"]
        or Decimal("0.00")
    )

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
    my_pending_claims = Transaction.objects.select_related(
        "created_by", "paid_by", "reimbursed_to"
    ).filter(
        is_claim=True,
        claim_status="PENDING",
    ).filter(
        Q(paid_by=request.user) | Q(reimbursed_to=request.user) | Q(created_by=request.user)
    ).order_by("-date", "-created_at")

    my_pending_claim_total = (
        my_pending_claims.aggregate(total=Sum("amount"))["total"]
        or Decimal("0.00")
    )

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

    # Recycling alternates starting from week beginning 2026-02-09
    base_recycling_week = timezone.datetime(2026, 2, 9).date()
    weeks_since_base = (this_week_start - base_recycling_week).days // 7

    if weeks_since_base % 2 == 0:
        recycling_note = "Mixed Recycling Week"
    else:
        recycling_note = "Glass Recycling Week"

    context = {
        "transactions": transactions,
        "total_in": total_in,
        "total_out": total_out,
        "balance": balance,
        "pending_claims": pending_claims,
        "my_pending_claims": my_pending_claims,
        "my_pending_claim_total": my_pending_claim_total,
        "pending_claim_total": pending_claim_total,
        "my_chore": my_chore,
        "weekly_roster": weekly_roster,
        "this_week_start": this_week_start,
        "recycling_note": recycling_note,
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





@login_required
def roster(request):
    week_param = request.GET.get("week")

    today = timezone.localdate()
    default_week_start = today - timedelta(days=today.weekday())

    week_start = parse_date(week_param) if week_param else default_week_start
    if week_start is None:
        week_start = default_week_start

    assignments = (
        RosterAssignment.objects.select_related("user", "chore")
        .filter(week_start=week_start)
        .order_by("chore__name", "user__username")
    )

    previous_week = week_start - timedelta(days=7)
    next_week = week_start + timedelta(days=7)

    base_week = timezone.datetime(2026, 2, 9).date()
    weeks_since = (week_start - base_week).days // 7

    if weeks_since % 2 == 0:
        recycling_note = "Mixed Recycling Week"
    else:
        recycling_note = "Glass Recycling Week"

    context = {
        "assignments": assignments,
        "week_start": week_start,
        "previous_week": previous_week,
        "next_week": next_week,
        "recycling_note": recycling_note,
    }
    return render(request, "flat/roster.html", context)

def help_page(request):
    return render(request, "flat/help.html")




@login_required
def receive_rent(request):
    if not (request.user.username.lower() == "stella" or request.user.is_staff):
        return redirect("dashboard")

    rent_data = [
        {"user_id": 5, "amount": Decimal("305.00")},
        {"user_id": 1, "amount": Decimal("325.00")},
        {"user_id": 3, "amount": Decimal("305.00")},
        {"user_id": 4, "amount": Decimal("325.00")},
        {"user_id": 2, "amount": Decimal("275.00")},
    ]

    if request.method == "POST":
        form = ReceiveRentForm(request.POST)
        if form.is_valid():
            selected_date = form.cleaned_data["date"]

            created_count = 0

            for item in rent_data:
                flatmate = User.objects.get(id=item["user_id"])

                Transaction.objects.create(
                    date=selected_date,
                    description="Rent + Expenses",
                    category="Rent + Expenses",
                    amount=item["amount"],
                    transaction_type="IN",
                    payment_source="TRANSFER",
                    created_by=request.user,
                    paid_by=flatmate,
                    notes=f"Bulk rent/expenses received for {flatmate.first_name or flatmate.username}",
                )
                created_count += 1

            messages.success(
                request,
                f"{created_count} rent transactions were recorded for {selected_date}."
            )
            return redirect("dashboard")
    else:
        form = ReceiveRentForm()

    context = {
        "form": form,
        "rent_data": rent_data,
    }
    return render(request, "flat/receive_rent.html", context)