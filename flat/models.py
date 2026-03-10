from django.db import models
from django.contrib.auth.models import User

class Chore(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


class RosterAssignment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    chore = models.ForeignKey(Chore, on_delete=models.CASCADE)
    week_start = models.DateField()

    def __str__(self):
        return f"{self.week_start} - {self.user.username} - {self.chore.name}"
    
class Transaction(models.Model):
    TRANSACTION_TYPE_CHOICES = [
        ("IN", "Money In"),
        ("OUT", "Money Out"),
    ]

    PAYMENT_SOURCE_CHOICES = [
        ("FLAT", "Flat Account/Card"),
        ("PERSONAL", "Paid Personally"),
        ("TRANSFER", "Bank Transfer"),
    ]

    CLAIM_STATUS_CHOICES = [
        ("NONE", "Not a Claim"),
        ("PENDING", "Pending"),
        ("PAID", "Paid Back"),
    ]

    date = models.DateField()
    description = models.CharField(max_length=255)
    category = models.CharField(max_length=100, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)

    transaction_type = models.CharField(
        max_length=3,
        choices=TRANSACTION_TYPE_CHOICES
    )

    payment_source = models.CharField(
        max_length=10,
        choices=PAYMENT_SOURCE_CHOICES,
        blank=True
    )

    created_by = models.ForeignKey(User, on_delete=models.CASCADE)

    is_claim = models.BooleanField(default=False)

    claim_status = models.CharField(
        max_length=10,
        choices=CLAIM_STATUS_CHOICES,
        default="NONE"
    )

    reimbursed_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reimbursement_transactions"
    )

    reimbursed_date = models.DateField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)

    def save(self, *args, **kwargs):
        if self.transaction_type == "OUT" and self.payment_source == "PERSONAL":
            self.is_claim = True
            if self.claim_status == "NONE":
                self.claim_status = "PENDING"
            if self.reimbursed_to is None:
                self.reimbursed_to = self.created_by
        else:
            self.is_claim = False
            self.claim_status = "NONE"
            self.reimbursed_to = None
            self.reimbursed_date = None

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.date} - {self.description} - {self.amount}"