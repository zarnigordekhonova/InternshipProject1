from django.db import transaction
from django.contrib import messages
from django.urls import reverse_lazy
from django.shortcuts import redirect
from django.views.generic.edit import CreateView
from django.http import JsonResponse, Http404
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required

from apps.applications.models import Application, Specialty, SpecialistsRequired, EquipmentRequired, EquipmentRequiredItem
from apps.applications.choices import ApplicationStatus
from apps.applications.forms import ApplicationForm, ApplicationBranchFormSet
from apps.applications.utils import generate_registration_number, send_application_email


def get_requirements_for_specialty(request):
    """
    Given a list of specialty IDs, returns the aggregated list of required 
    specialists and equipment with their details (name, minimum count).
    
    Updated to use the new EquipmentRequiredItem model for individual equipment counts.
    """
    if not request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.method != 'POST':
        raise Http404

    import json
    try:
        data = json.loads(request.body)
        specialty_ids = data.get('specialty_ids', [])
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON format'}, status=400)
    
    if not specialty_ids:
        return JsonResponse({'specialists': [], 'equipment': []})

    specialists_dict = {}
    equipment_dict = {}

    for specialty_id in specialty_ids:
        try:
            specialty = Specialty.objects.get(pk=specialty_id)
        except Specialty.DoesNotExist:
            continue
        
        # 1. Collect Specialist Requirements
        specialist_reqs = SpecialistsRequired.objects.filter(
            specialty=specialty
        ).select_related('required_specialists')
        
        for req in specialist_reqs:
            specialist_id = req.required_specialists.id
            specialist_title = req.required_specialists.title
            min_count = req.min_count
            
            if specialist_id in specialists_dict:
                specialists_dict[specialist_id]['min_count'] = max(
                    specialists_dict[specialist_id]['min_count'], 
                    min_count
                )
            else:
                specialists_dict[specialist_id] = {
                    'id': specialist_id,
                    'title': specialist_title,
                    'min_count': min_count
                }

        # 2. Collect Equipment Requirements (NEW LOGIC)
        try:
            equipment_req = EquipmentRequired.objects.get(specialty=specialty)
            # Get all equipment items with their individual counts
            equipment_items = EquipmentRequiredItem.objects.filter(
                equipment_required=equipment_req
            ).select_related('equipment')
            
            for item in equipment_items:
                equipment_id = item.equipment.id
                equipment_name = item.equipment.name
                min_count = item.min_count  # Individual count per equipment
                
                if equipment_id in equipment_dict:
                    equipment_dict[equipment_id]['min_count'] = max(
                        equipment_dict[equipment_id]['min_count'],
                        min_count
                    )
                else:
                    equipment_dict[equipment_id] = {
                        'id': equipment_id,
                        'name': equipment_name,
                        'min_count': min_count
                    }
        except EquipmentRequired.DoesNotExist:
            pass

    specialists_list = list(specialists_dict.values())
    equipment_list = list(equipment_dict.values())

    return JsonResponse({
        'specialists': specialists_list,
        'equipment': equipment_list,
    })


@method_decorator(login_required, name='dispatch') 
class ApplicationCreateView(CreateView):
    model = Application
    form_class = ApplicationForm
    template_name = 'applications/application_form.html'
    success_url = reverse_lazy("applications:application_list")

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        if self.request.POST:
            data['branch_formset'] = ApplicationBranchFormSet(
                self.request.POST, 
                self.request.FILES, 
                instance=self.object
            )
        else:
            data['branch_formset'] = ApplicationBranchFormSet(instance=self.object)
        return data

    def form_valid(self, form):
        context = self.get_context_data()
        branch_formset = context['branch_formset']

        with transaction.atomic():
            app_instance = form.instance
            
            if self.request.user.is_authenticated:
                app_instance.user = self.request.user

            if 'send_application' in self.request.POST:
                app_instance.status = ApplicationStatus.SUBMITTED
                if not app_instance.registration_number:
                    app_instance.registration_number = generate_registration_number()
            elif 'save_draft' in self.request.POST:
                app_instance.status = ApplicationStatus.DRAFT
            
            self.object = form.save()
            
            if branch_formset.is_valid():
                branch_formset.instance = self.object
                branch_formset.save()
            else:
                messages.error(
                    self.request, 
                    "Filial ma'lumotlarini saqlashda xato yuz berdi. Iltimos, xatolarni tuzating."
                )
                return self.form_invalid(form)

            if app_instance.status == ApplicationStatus.SUBMITTED:
                send_application_email(app_instance)
                messages.success(
                    self.request, 
                    f"Ariza muvaffaqiyatli yuborildi. Ro'yxatdan o'tish raqamingiz: {app_instance.registration_number}"
                )
            elif app_instance.status == ApplicationStatus.DRAFT:
                messages.info(self.request, "Ariza qoralama sifatida saqlandi.")

        return redirect(self.get_success_url())

    def form_invalid(self, form):
        context = self.get_context_data(form=form)
        messages.error(
            self.request, 
            "Arizani saqlashda xato yuz berdi. Iltimos, barcha xatolarni tuzating."
        )
        return self.render_to_response(context)
