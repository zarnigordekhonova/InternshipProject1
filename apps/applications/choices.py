from django.db.models import TextChoices
from django.utils.translation import gettext_lazy as _


class ApplicationStatus(TextChoices):
    DRAFT = ("draft", _("Draft"))
    SUBMITTED = ("submitted", _("Submitted"))
    PENDING = ("pending", _("Pending"))
    APPROVED = ("approved", _("Approved"))
    REJECTED = ("rejected", _("Rejected"))
