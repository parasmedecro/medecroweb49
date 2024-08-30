from django.contrib import admin
from .models import *
# Register your models here.
class DoctorAdmin(admin.ModelAdmin):
    pass
admin.site.register(Doctor, DoctorAdmin)

class PatientAdmin(admin.ModelAdmin):
    pass
admin.site.register(Patient, PatientAdmin)

class AppointmentAdmin(admin.ModelAdmin):
    pass
admin.site.register(Appointment, AppointmentAdmin)

class PatientDischargeDetailsAdmin(admin.ModelAdmin):
    pass
admin.site.register(PatientDischargeDetail, PatientDischargeDetailsAdmin)

class PatientReportAdmin(admin.ModelAdmin):
    pass
admin.site.register(PatientReport, PatientReportAdmin)

class LipidProfileAdmin(admin.ModelAdmin):
    pass
admin.site.register(LipidProfile, LipidProfileAdmin)

class PPBS_ReportsAdmin(admin.ModelAdmin):
    pass
admin.site.register(PPBS_Reports, PPBS_ReportsAdmin)

class FBS_ReportsAdmin(admin.ModelAdmin):
    pass
admin.site.register(FBS_Reports, FBS_ReportsAdmin)

class Vitamin_ReportsAdmin(admin.ModelAdmin):
    pass
admin.site.register(Vitamin_Reports, Vitamin_ReportsAdmin)
