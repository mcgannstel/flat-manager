from django.contrib import admin
from .models import Transaction, Chore, RosterAssignment


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = (
        "date",
        "description",
        "amount",
        "transaction_type",
        "payment_source",
        "paid_by",
        "created_by",
        "is_claim",
        "claim_status",
        "reimbursed_to",
        "reimbursed_date",
    )

    list_filter = (
        "transaction_type",
        "payment_source",
        "is_claim",
        "claim_status",
        "date",
    )

    search_fields = (
        "description",
        "category",
        "notes",
        "paid_by__username",
        "created_by__username",
        "reimbursed_to__username",
    )

    autocomplete_fields = (
        "created_by",
        "paid_by",
        "reimbursed_to",
    )

    date_hierarchy = "date"

    fieldsets = (
        (
            "Basic Information",
            {
                "fields": (
                    "date",
                    "description",
                    "category",
                    "amount",
                    "notes",
                )
            },
        ),
        (
            "Transaction Details",
            {
                "fields": (
                    "transaction_type",
                    "payment_source",
                    "created_by",
                    "paid_by",
                )
            },
        ),
        (
            "Claim Details",
            {
                "fields": (
                    "is_claim",
                    "claim_status",
                    "reimbursed_to",
                    "reimbursed_date",
                )
            },
        ),
        (
            "System",
            {
                "fields": ("created_at",)
            },
        ),
    )

    readonly_fields = ("created_at",)


@admin.register(Chore)
class ChoreAdmin(admin.ModelAdmin):
    list_display = ("name", "description")
    search_fields = ("name", "description")


@admin.register(RosterAssignment)
class RosterAssignmentAdmin(admin.ModelAdmin):
    list_display = ("week_start", "user", "chore")
    list_filter = ("week_start", "chore")
    search_fields = ("user__username", "user__first_name", "chore__name")
    autocomplete_fields = ("user", "chore")