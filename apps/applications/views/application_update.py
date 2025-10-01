import random
import string
from datetime import datetime
from django.db import transaction
from django.contrib import messages
from django.urls import reverse_lazy
from django.core.mail import send_mail
from django.views.generic import UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect, get_object_or_404

from apps.applications.choices import ApplicationStatus
from apps.applications.models import Application, ApplicationBranch
from apps.applications.forms import ApplicationForm, ApplicationBranchForm


class ApplicationUpdateView(LoginRequiredMixin, UpdateView):
    model = Application
    form_class = ApplicationForm
    template_name = 'applications/application_form.html'
    
    def get_success_url(self):
        return reverse_lazy('application_update', kwargs={'pk': self.object.pk})
    
    def get_queryset(self):
        return Application.objects.filter(user=self.request.user)
    
    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        
        # Prevent editing submitted applications
        if self.object.status != ApplicationStatus.DRAFT:
            messages.warning(request, "Yuborilgan arizani tahrirlash mumkin emas!")
            return redirect('application_detail', pk=self.object.pk)
        
        return super().get(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        try:
            application_branch = ApplicationBranch.objects.get(application=self.object)
        except ApplicationBranch.DoesNotExist:
            application_branch = None
        
        if self.request.POST:
            context['branch_form'] = ApplicationBranchForm(
                self.request.POST,
                instance=application_branch
            )
        else:
            context['branch_form'] = ApplicationBranchForm(instance=application_branch)
        
        context['form_title'] = "Arizani tahrirlash"
        context['is_draft'] = (self.object.status == ApplicationStatus.DRAFT)
        context['can_submit'] = (self.object.status == ApplicationStatus.DRAFT)
        return context
    
    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        
        submit_action = request.POST.get('action') == 'submit'
        
        if submit_action:
            return self.handle_submit()
        else:
            return self.handle_save()
    
    def handle_save(self):
        form = self.get_form()
        
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)
    
    def handle_submit(self):
        form = self.get_form()
        
        if not form.is_valid():
            messages.error(self.request, "Iltimos, barcha maydonlarni to'g'ri to'ldiring!")
            return self.form_invalid(form)
        
        validation_errors = self.validate_application_for_submission()
        
        if validation_errors:
            for error in validation_errors:
                messages.error(self.request, error)
            return self.form_invalid(form)
        
        context = self.get_context_data()
        branch_form = context['branch_form']
        
        if not branch_form.is_valid():
            messages.error(
                self.request,
                "Filial ma'lumotlarini to'ldiring. Filial va ixtisoslik turlarini tanlash majburiy."
            )
            return self.form_invalid(form)
        
        try:
            with transaction.atomic():
                self.object = form.save()
                
                branch_instance = branch_form.save(commit=False)
                branch_instance.application = self.object
                branch_instance.save()
                branch_form.save_m2m()
                
                self.object.registration_number = self.generate_registration_number()
                
                self.object.status = ApplicationStatus.PENDING
                self.object.save()
                
                self.send_application_notification()
            
            messages.success(
                self.request,
                f"Ariza muvaffaqiyatli yuborildi! Ro'yxatga olish raqami: {self.object.registration_number}"
            )
            return redirect('application_detail', pk=self.object.pk)
            
        except Exception as e:
            messages.error(self.request, f"Arizani yuborishda xatolik yuz berdi: {str(e)}")
            return self.form_invalid(form)
    
    def validate_application_for_submission(self):
        """Validate all required fields before submission"""
        errors = []
        
        required_fields = {
            'first_name': 'Ism',
            'last_name': 'Familiya',
            'paternal_name': 'Otasining ismi',
            'full_address': 'To\'liq manzil',
            'work_place': 'Ish joyi',
            'phone_number': 'Telefon raqami',
            'email': 'E-pochta',
            'document_type': 'Hujjat turi',
        }
        
        for field, label in required_fields.items():
            if not getattr(self.object, field):
                errors.append(f"{label} to'ldirilmagan!")
        
        try:
            application_branch = ApplicationBranch.objects.get(application=self.object)
        except ApplicationBranch.DoesNotExist:
            errors.append("Filial ma'lumotlari to'ldirilmagan!")
            return errors
        
        if not application_branch.branch:
            errors.append("Filial tanlanmagan!")
        
        if not application_branch.specialties.exists():
            errors.append("Kamida bitta ixtisoslik turini tanlash kerak!")
        
        return errors
    
    def generate_registration_number(self):
        """Generate unique registration number in format: APP-YYYYMMDD-XXXX"""
        date_part = datetime.now().strftime('%Y%m%d')
        random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
        registration_number = f"APP-{date_part}-{random_part}"
        
        while Application.objects.filter(registration_number=registration_number).exists():
            random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
            registration_number = f"APP-{date_part}-{random_part}"
        
        return registration_number
    
    def send_application_notification(self):
        """Send notification to user via email"""
        self.send_email_notification()
     
    
    def send_email_notification(self):
        """Send email notification to user"""
        try:
            branch_name = "N/A"
            if self.object.applicationbranch_set.exists():
                branch_name = self.object.applicationbranch_set.first().branch.name
            
            subject = f"Ariza qabul qilindi - {self.object.registration_number}"
            message = f"""
                        Hurmatli {self.object.first_name} {self.object.last_name},

                        Sizning arizangiz muvaffaqiyatli qabul qilindi.

                        Ro'yxatga olish raqami: {self.object.registration_number}
                        Filial: {branch_name}
                        Sana: {self.object.updated_at.strftime('%d.%m.%Y %H:%M')}

                        Arizangiz ko'rib chiqilmoqda. Natija haqida tez orada xabardor qilinasiz.

                        Hurmat bilan,
                        Ariza tizimi jamoasi
                                    """
            
            send_mail(
                subject=subject,
                message=message,
                from_email="zarnigor1008@gmail.com",
                recipient_list=[self.object.email],
                fail_silently=False,
            )
            
            print(f"Email yuborildi: {self.object.email}")
            
        except Exception as e:
            print(f"Email yuborishda xatolik: {e}")

    def form_valid(self, form):
        """Handle valid form (save as draft)"""
        context = self.get_context_data()
        branch_form = context['branch_form']
        
        if not branch_form.is_valid():
            messages.error(
                self.request,
                "Filial ma'lumotlarini to'ldiring. Filial va ixtisoslik turlarini tanlash majburiy."
            )
            return self.form_invalid(form)
        
        with transaction.atomic():
            self.object = form.save()
            
            branch_instance = branch_form.save(commit=False)
            branch_instance.application = self.object
            branch_instance.save()
            branch_form.save_m2m()
        
        messages.success(self.request, "Ariza muvaffaqiyatli saqlandi!")
        return redirect(self.get_success_url())
    
    def form_invalid(self, form):
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, f"{field}: {error}")
        return super().form_invalid(form)




