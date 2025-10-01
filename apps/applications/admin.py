from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from apps.applications.models import (
    Region, District, Branch, Specialty, Specialist, Equipment, 
    SpecialistsRequired, EquipmentRequired, Application, ApplicationBranch, EquipmentRequiredItem
)


class ApplicationBranchInline(admin.TabularInline):
    """Allows editing ApplicationBranch records directly within the Application form."""
    model = ApplicationBranch
    # Display the primary fields for context
    fields = ('branch', 'specialties', 'selected_specialists', 'selected_equipment')
    autocomplete_fields = ['branch'] 
    extra = 0
    min_num = 1 
    verbose_name = _("Associated Branch/Filial Details")
    verbose_name_plural = _("Associated Branches/Filial Details")


# --- Inline Definitions for Requirement Management (Specialty View) ---

class SpecialistsRequiredInline(admin.TabularInline):
    """Allows setting the minimum required specialists (by title and count) for a Specialty."""
    model = SpecialistsRequired
    extra = 1 # Start with one extra requirement field
    verbose_name = _("Specialist Requirement")
    verbose_name_plural = _("Minimal Specialist Requirements")
    autocomplete_fields = ['required_specialists'] # Link to Specialist model


class EquipmentRequiredItemInline(admin.TabularInline):
    model = EquipmentRequiredItem
    extra = 1
    fields = ('equipment', 'min_count')
    autocomplete_fields = ['equipment']


@admin.register(EquipmentRequired)
class EquipmentRequiredAdmin(admin.ModelAdmin):
    list_display = ('specialty', 'get_equipment_summary')
    search_fields = ('specialty__name',)
    inlines = [EquipmentRequiredItemInline]
    
    def get_equipment_summary(self, obj):
        items = obj.items.all()
        if not items:
            return "No equipment"
        return ", ".join([f"{item.min_count}x {item.equipment.name}" for item in items[:3]])
    get_equipment_summary.short_description = 'Equipment Summary'


# --- Admin Model Definitions ---

@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    """Admin configuration for the main Application model."""
    list_display = ('registration_number', 'last_name', 'first_name', 'phone_number', 'status', 'created_at')
    list_filter = ('status', 'document_type', 'created_at')
    search_fields = ('registration_number', 'last_name', 'first_name', 'paternal_name', 'phone_number', 'email')
    ordering = ('-created_at',)
    readonly_fields = ('registration_number', 'created_at', 'updated_at')
    
    # Use the inline to manage application branches/requirements directly
    inlines = [ApplicationBranchInline]

    # Group fields for better readability
    fieldsets = (
        (_('Application Status & Registration'), {
            'fields': ('user', 'status', 'registration_number'),
        }),
        (_('Applicant Personal Information (Mandatory Fields)'), {
            'fields': (('last_name', 'first_name', 'paternal_name'), ('phone_number', 'email'), 'full_address'),
        }),
        (_('Document Information'), {
            'fields': ('document_type', 'document_file'),
        }),
    )

@admin.register(Specialty)
class SpecialtyAdmin(admin.ModelAdmin):
    """Admin configuration for the Specialty model, showing its requirements."""
    list_display = ('name',)
    search_fields = ('name',)
    inlines = [SpecialistsRequiredInline]


@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    """Admin configuration for the Branch model."""
    list_display = ('branch_name', 'district')
    list_filter = ('district__region', 'district',)
    search_fields = ('branch_name', 'district__district_name')
    autocomplete_fields = ['district']

@admin.register(District)
class DistrictAdmin(admin.ModelAdmin):
    list_display = ('district_name', 'region')
    list_filter = ('region',)
    search_fields = ('district_name',)
    autocomplete_fields = ['region']

@admin.register(Region)
class RegionAdmin(admin.ModelAdmin):
    list_display = ('region_name',)
    search_fields = ('region_name',)

@admin.register(Specialist)
class SpecialistAdmin(admin.ModelAdmin):
    list_display = ('title',)
    search_fields = ('title',)

# --- FIX: Register Equipment with search_fields for autocomplete ---
@admin.register(Equipment)
class EquipmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name', )
