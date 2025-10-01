from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _

from apps.applications.choices import ApplicationStatus

CustomUser = get_user_model()


class Region(models.Model):
    region_name = models.CharField(max_length=100, unique=True, verbose_name=_("Region name"))

    def __str__(self):
        return self.region_name
    
    class Meta:
        verbose_name = _("Region")
        verbose_name_plural = _("Regions")


class District(models.Model):
    region = models.ForeignKey(
        "applications.Region", 
        on_delete=models.CASCADE, 
        related_name="regions",
        verbose_name=_("Region"),
        )
    district_name = models.CharField(max_length=100, verbose_name=_("District name"))

    def __str__(self):
        return (f"{self.district_name} | {self.region.region_name}")
    
    class Meta:
        verbose_name = _("District")
        verbose_name_plural = _("Districts")


class Branch(models.Model):
    district = models.ForeignKey(
        "applications.District", 
        on_delete=models.CASCADE, 
        verbose_name=_("District"),
        )
    branch_name = models.CharField(max_length=255, null=True, blank=True, verbose_name="Branch name")
    

    def __str__(self):
        return (f"{self.district} | {self.branch_name}")
    
    class Meta:
        verbose_name = _("Branch")
        verbose_name_plural = _("Branches")


class Specialty(models.Model):
    name = models.CharField(max_length=255, verbose_name=_("Specialty name"))

    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = _("Specialty")
        verbose_name_plural = _("Specialties")


class Specialist(models.Model):
    title = models.CharField(max_length=128, verbose_name=_("Specialist title"))

    def __str__(self):
        return self.title
    
    class Meta:
        verbose_name = _("Specialist")
        verbose_name_plural = _("Specialists")


class SpecialistsRequired(models.Model):
    specialty = models.ForeignKey(
        "applications.Specialty", 
        on_delete=models.CASCADE, 
        verbose_name=_("Specialty"))
    required_specialists = models.ForeignKey(
        "applications.Specialist",
        on_delete=models.CASCADE,
        verbose_name=_("Minimum required specialists"),
    )
    min_count = models.PositiveIntegerField(default=1, verbose_name=_("Minimum count"))

    def __str__(self):
        return f"{self.specialty.name}: Min. {self.min_count} x {self.required_specialists.title}"

    class Meta:
        verbose_name = _("Specialist Required")
        verbose_name_plural = _("Specialists Required")
        unique_together = ('specialty', 'required_specialists')


class Equipment(models.Model):
    name = models.CharField(max_length=255, verbose_name=_("Equipment name"))
    description = models.TextField(blank=True, verbose_name=_("Description"))

    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = _("Equipment")
        verbose_name_plural = _("Equipments")


class EquipmentRequired(models.Model):
    specialty = models.OneToOneField(
        "applications.Specialty",
        on_delete=models.CASCADE, 
        verbose_name=_("Specialty"))
    
    def __str__(self):
        return f"{self.specialty.name} - Equipment Requirements"

    class Meta:
        verbose_name = _("Equipment Required")
        verbose_name_plural = _("Equipments Required")


class EquipmentRequiredItem(models.Model):
    equipment_required = models.ForeignKey(
        "applications.EquipmentRequired",
        on_delete=models.CASCADE,
        related_name="items",
        verbose_name=_("Equipment Required")
    )
    equipment = models.ForeignKey(
        "applications.Equipment",
        on_delete=models.CASCADE,
        verbose_name=_("Equipment")
    )
    min_count = models.PositiveIntegerField(
        default=1,
        verbose_name=_("Minimum count")
    )

    def __str__(self):
        return f"{self.equipment.name} (Min: {self.min_count})"
    
    class Meta:
        verbose_name = _("Equipment Required Item")
        verbose_name_plural = _("Equipment Required Items")
        unique_together = ('equipment_required', 'equipment')


class Application(models.Model):
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="applications",
        verbose_name=_("User")
    )
    first_name = models.CharField(max_length=128, verbose_name=_("First name"))
    last_name = models.CharField(max_length=128, verbose_name=_("Last name"))
    paternal_name = models.CharField(max_length=128, verbose_name=_("Paternal name"))
    full_address = models.CharField(max_length=255, verbose_name=_("Full address"))
    phone_number = models.CharField(
        max_length=50,  
        validators=[
            RegexValidator(
                regex=r"^\+?1?\d{9,13}$",
                message="Phone number must be entered in the format: '+99001112233'. Up to 13 digits allowed.",
            )
        ],
        unique=True,
        verbose_name=_("Phone number")
    )
    email = models.EmailField(unique=True, verbose_name=_("Email"))
    document_type = models.CharField(max_length=50, verbose_name=_("Document type"))
    document_file = models.FileField(
        upload_to='documents/', 
        blank=True, 
        null=True,
        verbose_name=_("Document file"))
    registration_number = models.CharField(
        max_length=128, 
        blank=True, 
        null=True, 
        verbose_name=_("Registration number"))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    branches = models.ManyToManyField(
        "applications.Branch", 
        through='ApplicationBranch',
        verbose_name=_("Branches")
        )
    status = models.CharField(
        choices=ApplicationStatus.choices,
        default=ApplicationStatus.DRAFT)

    def __str__(self):
        return f"{self.registration_number}"
    
    class Meta:
        verbose_name = "Application"
        verbose_name_plural = "Applications"


class ApplicationBranch(models.Model):
    application = models.ForeignKey(
        "applications.Application", 
        on_delete=models.CASCADE, 
        verbose_name=_("Application")
        )
    branch = models.ForeignKey(
        "applications.Branch", 
        on_delete=models.CASCADE,
        verbose_name=_("Branch"),
        )
    specialties = models.ManyToManyField("applications.Specialty", verbose_name="Specialties")
    selected_specialists = models.ManyToManyField(
        "applications.Specialist",
        blank=True,
        verbose_name=_("Selected Specialists"),
        )
    selected_equipment = models.ManyToManyField(
        "applications.Equipment",
        blank=True,
        verbose_name=_("Selected Equipment"),
        )
    
    def __str__(self):
        return self.branch.branch_name     
    
    class Meta:
        verbose_name = "Application Branch"
        verbose_name = "Applications Branch"
