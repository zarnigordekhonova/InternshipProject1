from django import forms
from django.core.exceptions import ValidationError
from django.forms.models import inlineformset_factory
from django.utils.translation import gettext_lazy as _

from apps.applications.models import Application, ApplicationBranch


class ApplicationBranchForm(forms.ModelForm):
    form_prefix = forms.CharField(widget=forms.HiddenInput(), required=False)
    
    class Meta:
        model = ApplicationBranch
        fields = [
            'branch', 
            'specialties', 
            'selected_specialists', 
            'selected_equipment'
        ]
        widgets = {
            'specialties': forms.CheckboxSelectMultiple(),
            'selected_specialists': forms.CheckboxSelectMultiple(),
            'selected_equipment': forms.CheckboxSelectMultiple(),
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        if self.prefix:
            self.fields['form_prefix'].initial = self.prefix

        for field_name in self.fields:
            field = self.fields[field_name]
            
            if isinstance(field.widget, forms.Select) and not isinstance(field.widget, forms.SelectMultiple):
                current_classes = field.widget.attrs.get('class', '')
                if 'form-select' not in current_classes:
                    field.widget.attrs['class'] = f'{current_classes} form-select'.strip()
            
            elif isinstance(field.widget, forms.CheckboxSelectMultiple):
                field.widget.attrs['class'] = 'checkbox-group'
        
        self.fields['specialties'].required = True 

    def clean(self):
        cleaned_data = super().clean()
        
        specialties = cleaned_data.get('specialties')
        selected_specialists = cleaned_data.get('selected_specialists')
        selected_equipment = cleaned_data.get('selected_equipment')
        
        if self.has_changed():
            if cleaned_data.get('branch') and not cleaned_data.get('DELETE'): 
                if not specialties:
                    raise ValidationError(
                        _("Iltimos, filial uchun ixtisoslik turlarini tanlang."),
                        code='missing_specialties'
                    )

            if specialties and selected_specialists:
                self._validate_specialist_requirements(specialties, selected_specialists)
            
            if specialties and selected_equipment:
                self._validate_equipment_requirements(specialties, selected_equipment)
            
        return cleaned_data

    def _validate_specialist_requirements(self, specialties_qs, selected_specialists_qs):
        from apps.applications.models import SpecialistsRequired
        
        for specialty in specialties_qs:
            required_qs = SpecialistsRequired.objects.filter(specialty=specialty)
            
            for requirement in required_qs:
                required_title = requirement.required_specialists.title
                min_count = requirement.min_count
                
                selected_count = selected_specialists_qs.filter(title=required_title).count()
                
                if selected_count < min_count:
                    raise ValidationError(
                        _("%(specialty)s ixtisosligi uchun minimal talab qilingan mutaxassislar yetarli emas. \"%(title)s\" lavozimidan kamida %(min_count)s ta kiritilishi shart (Kiritilgani: %(selected_count)s).") % {
                            'specialty': specialty.name,
                            'title': required_title,
                            'min_count': min_count,
                            'selected_count': selected_count
                        },
                        code='insufficient_specialists'
                    )

    def _validate_equipment_requirements(self, specialties_qs, selected_equipment_qs):
        from apps.applications.models import EquipmentRequired, EquipmentRequiredItem
        
        for specialty in specialties_qs:
            try:
                equipment_req = EquipmentRequired.objects.get(specialty=specialty)
            except EquipmentRequired.DoesNotExist:
                continue
            
            # Get all required equipment items with their individual counts
            required_items = EquipmentRequiredItem.objects.filter(
                equipment_required=equipment_req
            ).select_related('equipment')
            
            # Check each required equipment item
            for item in required_items:
                equipment_name = item.equipment.name
                min_count = item.min_count
                
                # Count how many of this equipment type user selected
                selected_count = selected_equipment_qs.filter(name=equipment_name).count()
                
                if selected_count < min_count:
                    raise ValidationError(
                        _("%(specialty)s ixtisosligi uchun \"%(equipment)s\" dan kamida %(min_count)s ta kiritilishi shart (Kiritilgani: %(selected_count)s).") % {
                            'specialty': specialty.name,
                            'equipment': equipment_name,
                            'min_count': min_count,
                            'selected_count': selected_count
                        },
                        code='insufficient_equipment'
                    )


ApplicationBranchFormSet = inlineformset_factory(
    Application, 
    ApplicationBranch, 
    form=ApplicationBranchForm, 
    extra=1, 
    can_delete=True 
)
