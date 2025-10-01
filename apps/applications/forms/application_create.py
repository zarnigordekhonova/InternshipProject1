from django import forms
from django.utils.translation import gettext_lazy as _

from apps.applications.models import Application


class ApplicationForm(forms.ModelForm):
    class Meta:
        model = Application
        fields = [
            'first_name', 'last_name', 'paternal_name', 'phone_number', 
            'email', 'document_type', 'document_file', 'full_address'
        ]
        
    # Fayl hajmi va formatini tekshirishni shu yerda amalga oshiramiz (dastlabki TZ talabi)
    def clean_document_file(self):
        document_file = self.cleaned_data.get('document_file')
        
        if document_file:
            # 1. Hajm Tekshiruvi (Maksimal 10MB)
            MAX_FILE_SIZE = 10 * 1024 * 1024 # 10MB
            if document_file.size > MAX_FILE_SIZE:
                raise forms.ValidationError(_("Fayl hajmi 10 MB dan oshmasligi kerak."))
                
            # 2. Format Tekshiruvi
            # Fayl nomidan kengaytmani olish
            file_extension = document_file.name.split('.')[-1].lower()
            ALLOWED_EXTENSIONS = ['pdf', 'jpg', 'png']
            
            if file_extension not in ALLOWED_EXTENSIONS:
                raise forms.ValidationError(_("Faqat PDF, JPG va PNG formatlari ruxsat etiladi."))
                
        return document_file