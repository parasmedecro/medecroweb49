from django.shortcuts import render,redirect,reverse
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login
from . import forms,models
from django.db.models import Sum
from django.contrib.auth.models import Group
from django.http import HttpResponseRedirect
from django.core.mail import send_mail
from django.contrib.auth.decorators import login_required,user_passes_test
from datetime import datetime,timedelta,date
from django.conf import settings
from django.db.models import Q
from django.contrib import messages
import os
from django.shortcuts import render, get_object_or_404
import google.generativeai as genai
from dotenv import load_dotenv
import os
import google.generativeai as genai

# Load environment variables from .env file
load_dotenv()

# Create your views here.
def home_view(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect('afterlogin')
    return render(request,'index.html')


#for showing signup/login button for admin
def adminclick_view(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect('afterlogin')
    return render(request,'hospital/adminclick.html')


#for showing signup/login button for doctor
def doctorclick_view(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect('afterlogin')
    return render(request,'hospital/doctorclick.html')


#for showing signup/login button for patient
def patientclick_view(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect('afterlogin')
    return render(request,'hospital/patientclick.html')




def admin_signup_view(request):
    form=forms.AdminSigupForm()
    users_in_group = User.objects.filter(groups__name="ADMIN")
    user_names = [user.username for user in users_in_group]
    if request.method=='POST':
        if 'signup' in request.POST:
            form=forms.AdminSigupForm(request.POST)
            if form.is_valid():
                user=form.save()
                user.set_password(user.password)
                user.save()
                my_admin_group = Group.objects.get_or_create(name='ADMIN')
                my_admin_group[0].user_set.add(user)
                return HttpResponseRedirect('adminlogin')
        elif 'login' in request.POST:
            username= request.POST.get("username")
            password= request.POST.get("password")
            if username in user_names:
                user = authenticate(request,username=username,password=password)
                if user is not None:
                    if user.is_active:
                        login(request,user)
                        return redirect('afterlogin')
                else:
                    messages.error(request, 'Invalid username or password. Please try again')
            else:
                messages.error(request, 'Invalid username or password. Please try again')
    return render(request,'admin_login.html',{'form':form})




def doctor_signup_view(request):
    userForm=forms.DoctorUserForm()
    doctorForm=forms.DoctorForm()
    mydict={'userForm':userForm,'doctorForm':doctorForm}
    users_in_group = User.objects.filter(groups__name="DOCTOR")
    user_names = [user.username for user in users_in_group]
    if request.method=='POST':
        if 'signup' in request.POST:
            userForm=forms.DoctorUserForm(request.POST)
            doctorForm=forms.DoctorForm(request.POST,request.FILES)
            if userForm.is_valid() and doctorForm.is_valid():
                user=userForm.save()
                user.set_password(user.password)
                user.save()
                doctor=doctorForm.save(commit=False)
                doctor.user=user
                doctor=doctor.save()
                my_doctor_group = Group.objects.get_or_create(name='DOCTOR')
                my_doctor_group[0].user_set.add(user)
            return HttpResponseRedirect('doctorlogin')
        elif 'login' in request.POST:
            username= request.POST.get("username")
            password= request.POST.get("password")
            if username in user_names:
                user = authenticate(request,username=username,password=password)
                if user is not None:
                    if user.is_active:
                        login(request,user)
                        return redirect('afterlogin')
                else:
                    messages.error(request, 'Invalid username or password. Please try again')
            else:
                messages.error(request, 'Invalid username or password. Please try again')
    return render(request,'doctor_login.html',context=mydict)


def patient_signup_view(request):
    userForm=forms.PatientUserForm()
    patientForm=forms.PatientForm()
    mydict={'userForm':userForm,'patientForm':patientForm}
    users_in_group = User.objects.filter(groups__name="PATIENT")
    user_names = [user.username for user in users_in_group]
    print(user_names)
    if request.method=='POST':
        if 'signup' in request.POST:
            userForm=forms.PatientUserForm(request.POST)
            patientForm=forms.PatientForm(request.POST,request.FILES)
            if userForm.is_valid() and patientForm.is_valid():
                user=userForm.save()
                user.set_password(user.password)
                user.save()
                patient=patientForm.save(commit=False)
                patient.user=user
                patient.assignedDoctorId=request.POST.get('assignedDoctorId')
                patient=patient.save()
                my_patient_group = Group.objects.get_or_create(name='PATIENT')
                my_patient_group[0].user_set.add(user)
            return HttpResponseRedirect('patientlogin')
        elif 'login' in request.POST:
            username= request.POST.get("username")
            password= request.POST.get("password")
            if username in user_names:
                user = authenticate(request,username=username,password=password)
                if user is not None:
                    if user.is_active:
                        login(request,user)
                        return redirect('afterlogin')
                else:
                    messages.error(request, 'Invalid username or password. Please try again')
            else:
                messages.error(request, 'Invalid username or password. Please try again')
    return render(request,'patient_login.html',context=mydict)






#-----------for checking user is doctor , patient or admin
def is_admin(user):
    return user.groups.filter(name='ADMIN').exists()
def is_doctor(user):
    return user.groups.filter(name='DOCTOR').exists()
def is_patient(user):
    return user.groups.filter(name='PATIENT').exists()


#---------AFTER ENTERING CREDENTIALS WE CHECK WHETHER USERNAME AND PASSWORD IS OF ADMIN,DOCTOR OR PATIENT
def afterlogin_view(request):
    if is_admin(request.user):
        return redirect('admin-dashboard')
    elif is_doctor(request.user):
        accountapproval=models.Doctor.objects.all().filter(user_id=request.user.id,status=True)
        if accountapproval:
            return redirect('doctor-dashboard')
        else:
            return render(request,'hospital/doctor_wait_for_approval.html')
    elif is_patient(request.user):
        accountapproval=models.Patient.objects.all().filter(user_id=request.user.id,status=True)
        if accountapproval:
            return redirect('patient-dashboard')
        else:
            return render(request,'hospital/patient_wait_for_approval.html')








#---------------------------------------------------------------------------------
#------------------------ ADMIN RELATED VIEWS START ------------------------------
#---------------------------------------------------------------------------------
@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def admin_dashboard_view(request):
    #for both table in admin dashboard
    doctors=models.Doctor.objects.all().order_by('-id')
    patients=models.Patient.objects.all().order_by('-id')
    #for three cards
    doctorcount=models.Doctor.objects.all().filter(status=True).count()
    pendingdoctorcount=models.Doctor.objects.all().filter(status=False).count()

    patientcount=models.Patient.objects.all().filter(status=True).count()
    pendingpatientcount=models.Patient.objects.all().filter(status=False).count()

    appointmentcount=models.Appointment.objects.all().filter(status=True).count()
    pendingappointmentcount=models.Appointment.objects.all().filter(status=False).count()
    mydict={
    'doctors':doctors,
    'patients':patients,
    'doctorcount':doctorcount,
    'pendingdoctorcount':pendingdoctorcount,
    'patientcount':patientcount,
    'pendingpatientcount':pendingpatientcount,
    'appointmentcount':appointmentcount,
    'pendingappointmentcount':pendingappointmentcount,
    }
    return render(request,'hospital/admin_dashboard.html',context=mydict)


# this view for sidebar click on admin page
@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def admin_doctor_view(request):
    return render(request,'hospital/admin_doctor.html')



@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def admin_view_doctor_view(request):
    doctors=models.Doctor.objects.all().filter(status=True)
    return render(request,'hospital/admin_view_doctor.html',{'doctors':doctors})



@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def delete_doctor_from_hospital_view(request,pk):
    doctor=models.Doctor.objects.get(id=pk)
    user=models.User.objects.get(id=doctor.user_id)
    user.delete()
    doctor.delete()
    return redirect('admin-view-doctor')



@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def update_doctor_view(request,pk):
    doctor=models.Doctor.objects.get(id=pk)
    user=models.User.objects.get(id=doctor.user_id)

    userForm=forms.DoctorUserForm(instance=user)
    doctorForm=forms.DoctorForm(request.FILES,instance=doctor)
    mydict={'userForm':userForm,'doctorForm':doctorForm}
    if request.method=='POST':
        userForm=forms.DoctorUserForm(request.POST,instance=user)
        doctorForm=forms.DoctorForm(request.POST,request.FILES,instance=doctor)
        if userForm.is_valid() and doctorForm.is_valid():
            user=userForm.save()
            user.set_password(user.password)
            user.save()
            doctor=doctorForm.save(commit=False)
            doctor.status=True
            doctor.save()
            return redirect('admin-view-doctor')
    return render(request,'hospital/admin_update_doctor.html',context=mydict)




@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def admin_add_doctor_view(request):
    userForm=forms.DoctorUserForm()
    doctorForm=forms.DoctorForm()
    mydict={'userForm':userForm,'doctorForm':doctorForm}
    if request.method=='POST':
        userForm=forms.DoctorUserForm(request.POST)
        doctorForm=forms.DoctorForm(request.POST, request.FILES)
        if userForm.is_valid() and doctorForm.is_valid():
            user=userForm.save()
            user.set_password(user.password)
            user.save()

            doctor=doctorForm.save(commit=False)
            doctor.user=user
            doctor.status=True
            doctor.save()

            my_doctor_group = Group.objects.get_or_create(name='DOCTOR')
            my_doctor_group[0].user_set.add(user)

        return HttpResponseRedirect('admin-view-doctor')
    return render(request,'hospital/admin_add_doctor.html',context=mydict)




@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def admin_approve_doctor_view(request):
    #those whose approval are needed
    doctors=models.Doctor.objects.all().filter(status=False)
    return render(request,'hospital/admin_approve_doctor.html',{'doctors':doctors})


@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def approve_doctor_view(request,pk):
    doctor=models.Doctor.objects.get(id=pk)
    doctor.status=True
    doctor.save()
    return redirect(reverse('admin-approve-doctor'))


@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def reject_doctor_view(request,pk):
    doctor=models.Doctor.objects.get(id=pk)
    user=models.User.objects.get(id=doctor.user_id)
    user.delete()
    doctor.delete()
    return redirect('admin-approve-doctor')



@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def availability_view(request):
    doctors=models.Doctor.objects.all().filter(status=True)
    return render(request,'availability_view.html',{'doctors':doctors})



@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def avail_doctor(request,pk):
    doctor=models.Doctor.objects.get(id=pk)
    doctor.availability=True
    doctor.save()
    return redirect('availability')


@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def unavail_doctor(request,pk):
    doctor=models.Doctor.objects.get(id=pk)
    doctor.availability=False
    doctor.save()
    return redirect('availability')



@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def admin_view_doctor_specialisation_view(request):
    doctors=models.Doctor.objects.all().filter(status=True)
    return render(request,'hospital/admin_view_doctor_specialisation.html',{'doctors':doctors})



@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def admin_patient_view(request):
    return render(request,'hospital/admin_patient.html')



@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def admin_view_patient_view(request):
    patients=models.Patient.objects.all().filter(status=True)
    return render(request,'hospital/admin_view_patient.html',{'patients':patients})



@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def delete_patient_from_hospital_view(request,pk):
    patient=models.Patient.objects.get(id=pk)
    user=models.User.objects.get(id=patient.user_id)
    user.delete()
    patient.delete()
    return redirect('admin-view-patient')



@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def update_patient_view(request,pk):
    patient=models.Patient.objects.get(id=pk)
    user=models.User.objects.get(id=patient.user_id)

    userForm=forms.PatientUserForm(instance=user)
    patientForm=forms.PatientForm(request.FILES,instance=patient)
    mydict={'userForm':userForm,'patientForm':patientForm}
    if request.method=='POST':
        userForm=forms.PatientUserForm(request.POST,instance=user)
        patientForm=forms.PatientForm(request.POST,request.FILES,instance=patient)
        if userForm.is_valid() and patientForm.is_valid():
            user=userForm.save()
            user.set_password(user.password)
            user.save()
            patient=patientForm.save(commit=False)
            patient.status=True
            patient.assignedDoctorId=request.POST.get('assignedDoctorId')
            patient.save()
            return redirect('admin-view-patient')
    return render(request,'hospital/admin_update_patient.html',context=mydict)





@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def admin_add_patient_view(request):
    userForm=forms.PatientUserForm()
    patientForm=forms.PatientForm()
    mydict={'userForm':userForm,'patientForm':patientForm}
    if request.method=='POST':
        userForm=forms.PatientUserForm(request.POST)
        patientForm=forms.PatientForm(request.POST,request.FILES)
        if userForm.is_valid() and patientForm.is_valid():
            user=userForm.save()
            user.set_password(user.password)
            user.save()

            patient=patientForm.save(commit=False)
            patient.user=user
            patient.status=True
            patient.assignedDoctorId=request.POST.get('assignedDoctorId')
            patient.save()

            my_patient_group = Group.objects.get_or_create(name='PATIENT')
            my_patient_group[0].user_set.add(user)

        return HttpResponseRedirect('admin-view-patient')
    return render(request,'hospital/admin_add_patient.html',context=mydict)



#------------------FOR APPROVING PATIENT BY ADMIN----------------------
@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def admin_approve_patient_view(request):
    #those whose approval are needed
    patients=models.Patient.objects.all().filter(status=False)
    return render(request,'hospital/admin_approve_patient.html',{'patients':patients})



@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def approve_patient_view(request,pk):
    patient=models.Patient.objects.get(id=pk)
    patient.status=True
    patient.save()
    return redirect(reverse('admin-approve-patient'))



@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def reject_patient_view(request,pk):
    patient=models.Patient.objects.get(id=pk)
    user=models.User.objects.get(id=patient.user_id)
    user.delete()
    patient.delete()
    return redirect('admin-approve-patient')



#--------------------- FOR DISCHARGING PATIENT BY ADMIN START-------------------------
@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def admin_discharge_patient_view(request):
    patients=models.Patient.objects.all().filter(status=True)
    return render(request,'hospital/admin_discharge_patient.html',{'patients':patients})



@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def discharge_patient_view(request,pk):
    patient=models.Patient.objects.get(id=pk)
    days=(date.today()-patient.admitDate) #2 days, 0:00:00
    assignedDoctor=models.User.objects.all().filter(id=patient.assignedDoctorId)
    d=days.days # only how many day that is 2
    patientDict={
        'patientId':pk,
        'name':patient.get_name,
        'mobile':patient.mobile,
        'address':patient.address,
        'symptoms':patient.symptoms,
        'admitDate':patient.admitDate,
        'todayDate':date.today(),
        'day':d,
        'assignedDoctorName':assignedDoctor[0].first_name,
    }
    if request.method == 'POST':
        feeDict ={
            'roomCharge':int(request.POST['roomCharge'])*int(d),
            'doctorFee':request.POST['doctorFee'],
            'medicineCost' : request.POST['medicineCost'],
            'OtherCharge' : request.POST['OtherCharge'],
            'total':(int(request.POST['roomCharge'])*int(d))+int(request.POST['doctorFee'])+int(request.POST['medicineCost'])+int(request.POST['OtherCharge'])
        }
        patientDict.update(feeDict)
        #for updating to database PatientDischargeDetail (pDD)
        pDD=models.PatientDischargeDetail()
        pDD.patientId=pk
        pDD.patientName=patient.get_name
        pDD.assignedDoctorName=assignedDoctor[0].first_name
        pDD.address=patient.address
        pDD.mobile=patient.mobile
        pDD.symptoms=patient.symptoms
        pDD.admitDate=patient.admitDate
        pDD.releaseDate=date.today()
        pDD.daySpent=int(d)
        pDD.medicineCost=int(request.POST['medicineCost'])
        pDD.roomCharge=int(request.POST['roomCharge'])*int(d)
        pDD.doctorFee=int(request.POST['doctorFee'])
        pDD.OtherCharge=int(request.POST['OtherCharge'])
        pDD.total=(int(request.POST['roomCharge'])*int(d))+int(request.POST['doctorFee'])+int(request.POST['medicineCost'])+int(request.POST['OtherCharge'])
        pDD.save()
        return render(request,'hospital/patient_final_bill.html',context=patientDict)
    return render(request,'hospital/patient_generate_bill.html',context=patientDict)



#--------------for discharge patient bill (pdf) download and printing
import io
from xhtml2pdf import pisa
from django.template.loader import get_template
from django.template import Context
from django.http import HttpResponse


def render_to_pdf(template_src, context_dict):
    template = get_template(template_src)
    html  = template.render(context_dict)
    result = io.BytesIO()
    pdf = pisa.pisaDocument(io.BytesIO(html.encode("ISO-8859-1")), result)
    if not pdf.err:
        return HttpResponse(result.getvalue(), content_type='application/pdf')
    return



def download_pdf_view(request,pk):
    dischargeDetails=models.PatientDischargeDetail.objects.all().filter(patientId=pk).order_by('-id')[:1]
    dict={
        'patientName':dischargeDetails[0].patientName,
        'assignedDoctorName':dischargeDetails[0].assignedDoctorName,
        'address':dischargeDetails[0].address,
        'mobile':dischargeDetails[0].mobile,
        'symptoms':dischargeDetails[0].symptoms,
        'admitDate':dischargeDetails[0].admitDate,
        'releaseDate':dischargeDetails[0].releaseDate,
        'daySpent':dischargeDetails[0].daySpent,
        'medicineCost':dischargeDetails[0].medicineCost,
        'roomCharge':dischargeDetails[0].roomCharge,
        'doctorFee':dischargeDetails[0].doctorFee,
        'OtherCharge':dischargeDetails[0].OtherCharge,
        'total':dischargeDetails[0].total,
    }
    return render_to_pdf('hospital/download_bill.html',dict)



#-----------------APPOINTMENT START--------------------------------------------------------------------
@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def admin_appointment_view(request):
    return render(request,'hospital/admin_appointment.html')



@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def admin_view_appointment_view(request):
    appointments=models.Appointment.objects.all().filter(status=True)
    return render(request,'hospital/admin_view_appointment.html',{'appointments':appointments})



@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def admin_add_appointment_view(request):
    appointmentForm=forms.AppointmentForm()
    mydict={'appointmentForm':appointmentForm,}
    if request.method=='POST':
        appointmentForm=forms.AppointmentForm(request.POST)
        if appointmentForm.is_valid():
            appointment=appointmentForm.save(commit=False)
            appointment.doctorId=request.POST.get('doctorId')
            appointment.patientId=request.POST.get('patientId')
            appointment.doctorName=models.User.objects.get(id=request.POST.get('doctorId')).first_name
            appointment.patientName=models.User.objects.get(id=request.POST.get('patientId')).first_name
            appointment.appointmentDate=request.POST.get('appointment')
            appointment.status=True
            appointment.save()
        return HttpResponseRedirect('admin-view-appointment')
    return render(request,'hospital/admin_add_appointment.html',context=mydict)



@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def admin_approve_appointment_view(request):
    #those whose approval are needed
    appointments=models.Appointment.objects.all().filter(status=False)
    return render(request,'hospital/admin_approve_appointment.html',{'appointments':appointments})

from twilio.rest import Client
import pytz
from datetime import datetime, timezone, timedelta

@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def approve_appointment_view(request,pk):
    appointment=models.Appointment.objects.get(id=pk)
    print(appointment.appointmentDate)
    appointment.status=True
    appointment.save()
    #Notify Patient
    account_sid = 'ACb604cdff6ba558c3c2b0c563a69a9a02'
    auth_token = 'fcd5d895f608ed8d9cce2e09311045d4'
    client = Client(account_sid, auth_token)
    message = client.messages.create(
        to='+919137796495',
        from_='+18577676358',
        body='MEDSAFE\nHospital A:- Dear Yash, Your Appointment For Doctor Rajiv Has Been Approved!!',
        )
    print(message.sid)
    time=appointment.appointmentDate - timedelta(hours=1)
    original_time_str = str(time)
    print(original_time_str)
    original_time = datetime.strptime(original_time_str, '%Y-%m-%d %H:%M:%S%z')
    target_timezone = timezone(timedelta(hours=5, minutes=30))
    converted_time = original_time.replace(tzinfo=target_timezone)
    send_when=converted_time
    print(send_when)
    messaging_service_sid = 'MG076a2e29b121411761f642ee568be06e'  
    message = client.messages.create(
        from_=messaging_service_sid,
        to='+919137796495',  
        body='MEDSAFE\nHospital A:- Dear Yash, Your Appointment is in 1 Hour',
        schedule_type='fixed',
        send_at=send_when.isoformat(),
    )
    return redirect(reverse('admin-approve-appointment'))



@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def reject_appointment_view(request,pk):
    appointment=models.Appointment.objects.get(id=pk)
    appointment.delete()
    #Notify Patient

    client = Client('accountsid', 'auth_token')

    message = client.messages.create(
        to='+919137796495',
        from_='+18577676358',
        body='MEDSAFE\nHospital A:- Dear Yash, Your Appointment For Doctor Rajiv Has Been Rejected!!',
        )
    print(message.sid)
    return redirect('admin-approve-appointment')
#---------------------------------------------------------------------------------
#------------------------ ADMIN RELATED VIEWS END ------------------------------
#---------------------------------------------------------------------------------






#---------------------------------------------------------------------------------
#------------------------ DOCTOR RELATED VIEWS START ------------------------------
#---------------------------------------------------------------------------------
@login_required(login_url='doctorlogin')
@user_passes_test(is_doctor)
def doctor_dashboard_view(request):
    #for three cards
    patientcount=models.Patient.objects.all().filter(status=True,assignedDoctorId=request.user.id).count()
    appointmentcount=models.Appointment.objects.all().filter(status=True,doctorId=request.user.id).count()
    patientdischarged=models.PatientDischargeDetail.objects.all().distinct().filter(assignedDoctorName=request.user.first_name).count()

    #for  table in doctor dashboard
    appointments=models.Appointment.objects.all().filter(status=True,doctorId=request.user.id).order_by('-id')
    patientid=[]
    for a in appointments:
        patientid.append(a.patientId)
    patients=models.Patient.objects.all().filter(status=True,user_id__in=patientid).order_by('-id')
    appointments=zip(appointments,patients)
    mydict={
    'patientcount':patientcount,
    'appointmentcount':appointmentcount,
    'patientdischarged':patientdischarged,
    'appointments':appointments,
    'doctor':models.Doctor.objects.get(user_id=request.user.id), #for profile picture of doctor in sidebar
    }
    return render(request,'hospital/doctor_dashboard.html',context=mydict)



@login_required(login_url='doctorlogin')
@user_passes_test(is_doctor)
def doctor_patient_view(request):
    mydict={
    'doctor':models.Doctor.objects.get(user_id=request.user.id), #for profile picture of doctor in sidebar
    }
    return render(request,'hospital/doctor_patient.html',context=mydict)





@login_required(login_url='doctorlogin')
@user_passes_test(is_doctor)
def doctor_view_patient_view(request):
    patients=models.Patient.objects.all().filter(status=True,assignedDoctorId=request.user.id)
    doctor=models.Doctor.objects.get(user_id=request.user.id) #for profile picture of doctor in sidebar
    return render(request,'hospital/doctor_view_patient.html',{'patients':patients,'doctor':doctor})


@login_required(login_url='doctorlogin')
@user_passes_test(is_doctor)
def search_view(request):
    doctor=models.Doctor.objects.get(user_id=request.user.id) #for profile picture of doctor in sidebar
    # whatever user write in search box we get in query
    query = request.GET['query']
    patients=models.Patient.objects.all().filter(status=True,assignedDoctorId=request.user.id).filter(Q(symptoms__icontains=query)|Q(user__first_name__icontains=query))
    return render(request,'hospital/doctor_view_patient.html',{'patients':patients,'doctor':doctor})



@login_required(login_url='doctorlogin')
@user_passes_test(is_doctor)
def doctor_view_discharge_patient_view(request):
    dischargedpatients=models.PatientDischargeDetail.objects.all().distinct().filter(assignedDoctorName=request.user.first_name)
    doctor=models.Doctor.objects.get(user_id=request.user.id) #for profile picture of doctor in sidebar
    return render(request,'hospital/doctor_view_discharge_patient.html',{'dischargedpatients':dischargedpatients,'doctor':doctor})



@login_required(login_url='doctorlogin')
@user_passes_test(is_doctor)
def doctor_appointment_view(request):
    doctor=models.Doctor.objects.get(user_id=request.user.id) #for profile picture of doctor in sidebar
    return render(request,'hospital/doctor_appointment.html',{'doctor':doctor})



@login_required(login_url='doctorlogin')
@user_passes_test(is_doctor)
def doctor_view_appointment_view(request):
    doctor=models.Doctor.objects.get(user_id=request.user.id) #for profile picture of doctor in sidebar
    appointments=models.Appointment.objects.all().filter(status=True,doctorId=request.user.id)
    patientid=[]
    for a in appointments:
        patientid.append(a.patientId)
    patients=models.Patient.objects.all().filter(status=True,user_id__in=patientid)
    appointments=zip(appointments,patients)
    return render(request,'hospital/doctor_view_appointment.html',{'appointments':appointments,'doctor':doctor})



@login_required(login_url='doctorlogin')
@user_passes_test(is_doctor)
def doctor_delete_appointment_view(request):
    doctor=models.Doctor.objects.get(user_id=request.user.id) #for profile picture of doctor in sidebar
    appointments=models.Appointment.objects.all().filter(status=True,doctorId=request.user.id)
    patientid=[]
    for a in appointments:
        patientid.append(a.patientId)
    patients=models.Patient.objects.all().filter(status=True,user_id__in=patientid)
    appointments=zip(appointments,patients)
    return render(request,'hospital/doctor_delete_appointment.html',{'appointments':appointments,'doctor':doctor})



@login_required(login_url='doctorlogin')
@user_passes_test(is_doctor)
def delete_appointment_view(request,pk):
    appointment=models.Appointment.objects.get(id=pk)
    appointment.delete()
    doctor=models.Doctor.objects.get(user_id=request.user.id) #for profile picture of doctor in sidebar
    appointments=models.Appointment.objects.all().filter(status=True,doctorId=request.user.id)
    patientid=[]
    for a in appointments:
        patientid.append(a.patientId)
    patients=models.Patient.objects.all().filter(status=True,user_id__in=patientid)
    appointments=zip(appointments,patients)
    return render(request,'hospital/doctor_delete_appointment.html',{'appointments':appointments,'doctor':doctor})



#---------------------------------------------------------------------------------
#------------------------ DOCTOR RELATED VIEWS END ------------------------------
#---------------------------------------------------------------------------------






#---------------------------------------------------------------------------------
#------------------------ PATIENT RELATED VIEWS START ------------------------------
#---------------------------------------------------------------------------------
@login_required(login_url='patientlogin')
@user_passes_test(is_patient)
def patient_dashboard_view(request):
    patient=models.Patient.objects.get(user_id=request.user.id)
    doctor=models.Doctor.objects.get(user_id=patient.assignedDoctorId)
    mydict={
    'patient':patient,
    'doctorName':doctor.get_name,
    'doctorMobile':doctor.mobile,
    'doctorAddress':doctor.address,
    'symptoms':patient.symptoms,
    'doctorDepartment':doctor.department,
    'admitDate':patient.admitDate,
    }
    return render(request,'hospital/patient_dashboard.html',context=mydict)



@login_required(login_url='patientlogin')
@user_passes_test(is_patient)
def patient_appointment_view(request):
    patient=models.Patient.objects.get(user_id=request.user.id) #for profile picture of patient in sidebar
    return render(request,'hospital/patient_appointment.html',{'patient':patient})



@login_required(login_url='patientlogin')
@user_passes_test(is_patient)
def patient_book_appointment_view(request):
    appointmentForm=forms.PatientAppointmentForm()
    patient=models.Patient.objects.get(user_id=request.user.id) #for profile picture of patient in sidebar
    message=None
    mydict={'appointmentForm':appointmentForm,'patient':patient,'message':message}
    if request.method=='POST':
        appointmentForm=forms.PatientAppointmentForm(request.POST)
        if appointmentForm.is_valid():
            print(request.POST.get('doctorId'))
            desc=request.POST.get('description')

            doctor=models.Doctor.objects.get(user_id=request.POST.get('doctorId'))
            
            appointment=appointmentForm.save(commit=False)
            appointment.doctorId=request.POST.get('doctorId')
            appointment.patientId=request.user.id #----user can choose any patient but only their info will be stored
            appointment.doctorName=models.User.objects.get(id=request.POST.get('doctorId')).first_name
            appointment.patientName=request.user.first_name #----user can choose any patient but only their info will be stored
            appointment.appointmentDate=request.POST.get('appointment')
            appointment.status=False
            appointment.save()
        return HttpResponseRedirect('patient-view-appointment')
    return render(request,'hospital/patient_book_appointment.html',context=mydict)



def patient_view_doctor_view(request):
    doctors=models.Doctor.objects.all().filter(status=True)
    patient=models.Patient.objects.get(user_id=request.user.id) #for profile picture of patient in sidebar
    return render(request,'hospital/patient_view_doctor.html',{'patient':patient,'doctors':doctors})



def search_doctor_view(request):
    patient=models.Patient.objects.get(user_id=request.user.id) #for profile picture of patient in sidebar
    
    # whatever user write in search box we get in query
    query = request.GET['query']
    doctors=models.Doctor.objects.all().filter(status=True).filter(Q(department__icontains=query)| Q(user__first_name__icontains=query))
    return render(request,'hospital/patient_view_doctor.html',{'patient':patient,'doctors':doctors})




@login_required(login_url='patientlogin')
@user_passes_test(is_patient)
def patient_view_appointment_view(request):
    patient=models.Patient.objects.get(user_id=request.user.id) #for profile picture of patient in sidebar
    appointments=models.Appointment.objects.all().filter(patientId=request.user.id)
    return render(request,'hospital/patient_view_appointment.html',{'appointments':appointments,'patient':patient})



@login_required(login_url='patientlogin')
@user_passes_test(is_patient)
def patient_discharge_view(request):
    patient=models.Patient.objects.get(user_id=request.user.id) #for profile picture of patient in sidebar
    dischargeDetails=models.PatientDischargeDetail.objects.all().filter(patientId=patient.id).order_by('-id')[:1]
    patientDict=None
    if dischargeDetails:
        patientDict ={
        'is_discharged':True,
        'patient':patient,
        'patientId':patient.id,
        'patientName':patient.get_name,
        'assignedDoctorName':dischargeDetails[0].assignedDoctorName,
        'address':patient.address,
        'mobile':patient.mobile,
        'symptoms':patient.symptoms,
        'admitDate':patient.admitDate,
        'releaseDate':dischargeDetails[0].releaseDate,
        'daySpent':dischargeDetails[0].daySpent,
        'medicineCost':dischargeDetails[0].medicineCost,
        'roomCharge':dischargeDetails[0].roomCharge,
        'doctorFee':dischargeDetails[0].doctorFee,
        'OtherCharge':dischargeDetails[0].OtherCharge,
        'total':dischargeDetails[0].total,
        }
        print(patientDict)
    else:
        patientDict={
            'is_discharged':False,
            'patient':patient,
            'patientId':request.user.id,
        }
    return render(request,'hospital/patient_discharge.html',context=patientDict)



@login_required(login_url='patientlogin')
@user_passes_test(is_patient)
def patient_report_vitamin_view(request):
    patient = get_object_or_404(models.Patient, user=request.user) #for profile picture of patient in sidebar
    reportDetails=models.Vitamin_Reports.objects.filter(patient=patient)
    patientDict=None
    if reportDetails:
        patientDict ={
        'patient':patient,
        'patientName':reportDetails[0].patient,
        'assignedDoctorName':reportDetails[0].assignedDoctorName,
        'address':reportDetails[0].address,
        'mobile':reportDetails[0].mobile,
        'symptoms':reportDetails[0].symptoms,
        'admitDate':reportDetails[0].admitDate,
        'todayDate':reportDetails[0].todayDate,
        'VitaminD12':reportDetails[0].VitaminD12,
        'VitaminD3':reportDetails[0].VitaminD3,
        }
    else:
        patientDict={
            'patient':patient,
            'patientId':request.user.id,
        }
    return render(request,'hospital/patient_report_vitamin_view.html',context=patientDict)


@login_required(login_url='patientlogin')
@user_passes_test(is_patient)
def patient_report_ppbs_view(request):
    patient = get_object_or_404(models.Patient, user=request.user) #for profile picture of patient in sidebar
    reportDetails=models.PPBS_Reports.objects.filter(patient=patient)
    patientDict=None
    if reportDetails:
        patientDict ={
        'patient':patient,
        'patientName':reportDetails[0].patient,
        'assignedDoctorName':reportDetails[0].assignedDoctorName,
        'address':reportDetails[0].address,
        'mobile':reportDetails[0].mobile,
        'symptoms':reportDetails[0].symptoms,
        'admitDate':reportDetails[0].admitDate,
        'todayDate':reportDetails[0].todayDate,
        'PostPrandialBloodSugar':reportDetails[0].PostPrandialBloodSugar,
        }
    else:
        patientDict={
            'patient':patient,
            'patientId':request.user.id,
        }
    return render(request,'hospital/patient_report_ppbs_view.html',context=patientDict)


@login_required(login_url='patientlogin')
@user_passes_test(is_patient)
def patient_report_fbs_view(request):
    patient = get_object_or_404(models.Patient, user=request.user) #for profile picture of patient in sidebar
    reportDetails=models.FBS_Reports.objects.filter(patient=patient)
    patientDict=None
    if reportDetails:
        patientDict ={
        'patient':patient,
        'patientName':reportDetails[0].patient,
        'assignedDoctorName':reportDetails[0].assignedDoctorName,
        'address':reportDetails[0].address,
        'mobile':reportDetails[0].mobile,
        'symptoms':reportDetails[0].symptoms,
        'admitDate':reportDetails[0].admitDate,
        'todayDate':reportDetails[0].todayDate,
        'FastingBloodSugar':reportDetails[0].FastingBloodSugar,
        }
    else:
        patientDict={
            'patient':patient,
            'patientId':request.user.id,
        }
    return render(request,'hospital/patient_report_fbs_view.html',context=patientDict)


@login_required(login_url='patientlogin')
@user_passes_test(is_patient)
def patient_report_lipid_view(request):
    patient = get_object_or_404(models.Patient, user=request.user) #for profile picture of patient in sidebar
    reportDetails=models.LipidProfile.objects.filter(patient=patient)
    patientDict=None
    if reportDetails:
        patientDict ={
        'patient':patient,
        'patientName':patient.get_name,
        'patientId':patient.id,
        'assignedDoctorName':reportDetails[0].assignedDoctorName,
        'address':reportDetails[0].address,
        'mobile':reportDetails[0].mobile,
        'symptoms':reportDetails[0].symptoms,
        'admitDate':reportDetails[0].admitDate,
        'todayDate':reportDetails[0].todayDate,
        'Cholestrol':reportDetails[0].Cholestrol,
        'Triglyceride':reportDetails[0].Triglyceride,
        'Ldl_cholestrol':reportDetails[0].Ldl_cholestrol,
        'Hdl_cholestrol':reportDetails[0].Hdl_cholestrol,
        'VLDL':reportDetails[0].VLDL,
        'CHOL_HDL_ratio':reportDetails[0].CHOL_HDL_ratio,
        'LDL_HDL_ratio':reportDetails[0].LDL_HDL_ratio,
        }
    else:
        patientDict={
            'patient':patient,
            'patientId':request.user.id,
        }
    return render(request,'hospital/patient_report_lipid_view.html',context=patientDict)


# @login_required(login_url='patientlogin')
# @user_passes_test(is_patient)
# def patient_reports(request):
#     patient=models.Patient.objects.get(user_id=request.user.id) #for profile picture of patient in sidebar
#     reports=models.PatientReport.objects.all().filter(patientName=patient.get_name)
#     return render(request,'hospital/patient_view_reports.html',{'reports':reports,'patient':patient})


#------------------------ PATIENT RELATED VIEWS END ------------------------------
#---------------------------------------------------------------------------------








#---------------------------------------------------------------------------------
#------------------------ ABOUT US AND CONTACT US VIEWS START ------------------------------
#---------------------------------------------------------------------------------
def aboutus_view(request):
    return render(request,'hospital/aboutus.html')

def contactus_view(request):
    sub = forms.ContactusForm()
    if request.method == 'POST':
        sub = forms.ContactusForm(request.POST)
        if sub.is_valid():
            email = sub.cleaned_data['Email']
            name=sub.cleaned_data['Name']
            message = sub.cleaned_data['Message']
            send_mail(str(name)+' || '+str(email),message,settings.EMAIL_HOST_USER, settings.EMAIL_RECEIVING_USER, fail_silently = False)
            return render(request, 'hospital/contactussuccess.html')
    return render(request, 'hospital/contactus.html', {'form':sub})


def patient_medtube(request):
    return render(request,'hospital/patient_medtube.html')

def manage_medtube(request):
    return render(request,'hospital/manage.html')

def upload_medtube(request):
    return render(request,'hospital/upload.html')


@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def admin_patient_report_view(request):
    patients=models.Patient.objects.all().filter(status=True)
    return render(request,'hospital/admin_patient_report_view.html',{'patients':patients})



@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def admin_patient_report_generate_lipid(request,pk):
    patient=models.Patient.objects.get(id=pk)
    assignedDoctor=models.User.objects.all().filter(id=patient.assignedDoctorId)
   
    patientLipidDict={
        'patientId':pk,
        'name':patient.get_name,
        'mobile':patient.mobile,
        'address':patient.address,
        'symptoms':patient.symptoms,
        'admitDate':patient.admitDate,
        'todayDate':date.today(),
        'assignedDoctorName':assignedDoctor[0].first_name,
    }
    if request.method == 'POST':
        ReportDic ={
            'Cholestrol':request.POST['Cholestrol'],
            'Triglyceride':request.POST['Triglyceride'],
            'Ldl_cholestrol' : request.POST['Ldl_cholestrol'],
            'Hdl_cholestrol':request.POST['Hdl_cholestrol'],
            'VLDL':request.POST['VLDL'],
            'CHOL_HDL_ratio':request.POST['CHOL_HDL_ratio'],
            'LDL_HDL_ratio':request.POST['LDL_HDL_ratio'],
        }
        patientLipidDict.update(ReportDic)
        #for updating to database PatientDischargeDetail (pLD)
        pLD=models.LipidProfile()
        pLD.patientId=pk
        pLD.patient=patient
        pLD.assignedDoctorName=assignedDoctor[0].first_name
        pLD.address=patient.address
        pLD.mobile=patient.mobile
        pLD.symptoms=patient.symptoms
        pLD.admitDate=patient.admitDate
        pLD.todayDate=date.today()
        pLD.Cholestrol=request.POST['Cholestrol']
        pLD.Triglyceride=request.POST['Triglyceride']
        pLD.Ldl_cholestrol=request.POST['Ldl_cholestrol']
        pLD.Hdl_cholestrol=request.POST['Hdl_cholestrol'] 
        pLD.VLDL=request.POST['VLDL']
        pLD.CHOL_HDL_ratio=request.POST['CHOL_HDL_ratio']
        pLD.LDL_HDL_ratio=request.POST['LDL_HDL_ratio']
        pLD.save()
        return render(request,'hospital/admin_patient_report_generate_view_lipid.html',context=patientLipidDict)
    return render(request,'hospital/admin_patient_lipid_report_generate.html',context=patientLipidDict)


@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def admin_patient_report_generate_ppbs(request,pk):
    patient=models.Patient.objects.get(id=pk)
    assignedDoctor=models.User.objects.all().filter(id=patient.assignedDoctorId)
   
    patientppbsDict={
        'patientId':pk,
        'name':patient.get_name,
        'mobile':patient.mobile,
        'address':patient.address,
        'symptoms':patient.symptoms,
        'admitDate':patient.admitDate,
        'todayDate':date.today(),
        'assignedDoctorName':assignedDoctor[0].first_name,
    }
    if request.method == 'POST':
        ReportDic ={
            'PostPrandialBloodSugar':request.POST['PostPrandialBloodSugar'],
        }
        patientppbsDict.update(ReportDic)
        #for updating to database PatientDischargeDetail (pLD)
        pPD=models.PPBS_Reports()
        pPD.patientId=pk
        pPD.patient=patient
        pPD.assignedDoctorName=assignedDoctor[0].first_name
        pPD.address=patient.address
        pPD.mobile=patient.mobile
        pPD.symptoms=patient.symptoms
        pPD.admitDate=patient.admitDate
        pPD.todayDate=date.today()
        pPD.PostPrandialBloodSugar=request.POST['PostPrandialBloodSugar']
        pPD.save()
        return render(request,'hospital/admin_patient_report_generate_view_ppbs.html',context=patientppbsDict)
    return render(request,'hospital/admin_patient_ppbs_report_generate.html',context=patientppbsDict)


@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def admin_patient_report_generate_fbs(request,pk):
    patient=models.Patient.objects.get(id=pk)
    assignedDoctor=models.User.objects.all().filter(id=patient.assignedDoctorId)
   
    patientppbsDict={
        'patientId':pk,
        'name':patient.get_name,
        'mobile':patient.mobile,
        'address':patient.address,
        'symptoms':patient.symptoms,
        'admitDate':patient.admitDate,
        'todayDate':date.today(),
        'assignedDoctorName':assignedDoctor[0].first_name,
    }
    if request.method == 'POST':
        ReportDic ={
            'FastingBloodSugar':request.POST['FastingBloodSugar'],
        }
        patientppbsDict.update(ReportDic)
        #for updating to database PatientDischargeDetail (pLD)
        pPD=models.FBS_Reports()
        pPD.patientId=pk
        pPD.patient=patient
        pPD.assignedDoctorName=assignedDoctor[0].first_name
        pPD.address=patient.address
        pPD.mobile=patient.mobile
        pPD.symptoms=patient.symptoms
        pPD.admitDate=patient.admitDate
        pPD.todayDate=date.today()
        pPD.FastingBloodSugar=request.POST['FastingBloodSugar']
        pPD.save()
        return render(request,'hospital/admin_patient_report_generate_view_fbs.html',context=patientppbsDict)
    return render(request,'hospital/admin_patient_fbs_report_generate.html',context=patientppbsDict)


@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def admin_patient_report_generate_vitamin(request,pk):
    patient=models.Patient.objects.get(id=pk)
    assignedDoctor=models.User.objects.all().filter(id=patient.assignedDoctorId)
   
    patientppbsDict={
        'patientId':pk,
        'name':patient.get_name,
        'mobile':patient.mobile,
        'address':patient.address,
        'symptoms':patient.symptoms,
        'admitDate':patient.admitDate,
        'todayDate':date.today(),
        'assignedDoctorName':assignedDoctor[0].first_name,
    }
    if request.method == 'POST':
        ReportDic ={
            'VitaminD12':request.POST['VitaminD12'],
            'VitaminD3':request.POST['VitaminD3'],
        }
        patientppbsDict.update(ReportDic)
        #for updating to database PatientDischargeDetail (pLD)
        pPD=models.Vitamin_Reports()
        pPD.patientId=pk
        pPD.patient=patient
        pPD.assignedDoctorName=assignedDoctor[0].first_name
        pPD.address=patient.address
        pPD.mobile=patient.mobile
        pPD.symptoms=patient.symptoms
        pPD.admitDate=patient.admitDate
        pPD.todayDate=date.today()
        pPD.VitaminD12=request.POST['VitaminD12']
        pPD.VitaminD3=request.POST['VitaminD3']
        pPD.save()
        return render(request,'hospital/admin_patient_report_generate_view_vitamin.html',context=patientppbsDict)
    return render(request,'hospital/admin_patient_vitamin_report_generate.html',context=patientppbsDict)




def report_pdf_view_lipid(request,pk):
    reportDetails=models.LipidProfile.objects.all().filter(patientId=pk).order_by('-id')[:1]
    dict={
        'patientName':reportDetails[0].patient,
        'assignedDoctorName':reportDetails[0].assignedDoctorName,
        'address':reportDetails[0].address,
        'mobile':reportDetails[0].mobile,
        'symptoms':reportDetails[0].symptoms,
        'admitDate':reportDetails[0].admitDate,
        'todayDate':reportDetails[0].todayDate,
        'Cholestrol':reportDetails[0].Cholestrol,
        'Triglyceride':reportDetails[0].Triglyceride,
        'Ldl_cholestrol':reportDetails[0].Ldl_cholestrol,
        'Hdl_cholestrol':reportDetails[0].Hdl_cholestrol,
        'VLDL':reportDetails[0].VLDL,
        'CHOL_HDL_ratio':reportDetails[0].CHOL_HDL_ratio,
        'LDL_HDL_ratio':reportDetails[0].LDL_HDL_ratio,
    }
    return render_to_pdf('hospital/report_lipid.html',dict)


def report_pdf_view_ppbs(request,pk):
    reportDetails=models.PPBS_Reports.objects.all().filter(patientId=pk).order_by('-id')[:1]
    dict={
        'patientName':reportDetails[0].patient,
        'assignedDoctorName':reportDetails[0].assignedDoctorName,
        'address':reportDetails[0].address,
        'mobile':reportDetails[0].mobile,
        'symptoms':reportDetails[0].symptoms,
        'admitDate':reportDetails[0].admitDate,
        'todayDate':reportDetails[0].todayDate,
        'PostPrandialBloodSugar':reportDetails[0].PostPrandialBloodSugar,
    }
    return render_to_pdf('hospital/report_ppbs.html',dict)


def report_pdf_view_vitamin(request,pk):
    reportDetails=models.Vitamin_Reports.objects.all().filter(patientId=pk).order_by('-id')[:1]
    dict={
        'patientName':reportDetails[0].patient,
        'assignedDoctorName':reportDetails[0].assignedDoctorName,
        'address':reportDetails[0].address,
        'mobile':reportDetails[0].mobile,
        'symptoms':reportDetails[0].symptoms,
        'admitDate':reportDetails[0].admitDate,
        'todayDate':reportDetails[0].todayDate,
        'VitaminD12':reportDetails[0].VitaminD12,
        'VitaminD3':reportDetails[0].VitaminD3,
    }
    return render_to_pdf('hospital/report_vitamin.html',dict)


def report_pdf_view_fbs(request,pk):
    reportDetails=models.FBS_Reports.objects.all().filter(patientId=pk).order_by('-id')[:1]
    dict={
        'patientName':reportDetails[0].patient,
        'assignedDoctorName':reportDetails[0].assignedDoctorName,
        'address':reportDetails[0].address,
        'mobile':reportDetails[0].mobile,
        'symptoms':reportDetails[0].symptoms,
        'admitDate':reportDetails[0].admitDate,
        'todayDate':reportDetails[0].todayDate,
        'FastingBloodSugar':reportDetails[0].FastingBloodSugar,
    }
    return render_to_pdf('hospital/report_fbs.html',dict)

# chatbot/views.py

# Configure Google Gemini API
genai.configure(api_key=os.environ["GEMINI_API_KEY"])

generation_config = {
    "temperature": 1,
    "top_p": 0.95,
    "top_k": 64,
    "max_output_tokens": 8192,
    "response_mime_type": "text/plain",
}

@login_required(login_url='patientlogin')
@user_passes_test(is_patient)
def chat_gemini(request):
    patient=models.Patient.objects.get(user_id=request.user.id) 
    response_text = ""
    if request.method == "POST":
        user_input = request.POST.get("user_input", "")
        model = genai.GenerativeModel(
            model_name="gemini-1.0-pro-001",
            generation_config=generation_config,
        )

        chat_session = model.start_chat(
            history=[]
        )
        context = f"You are a medical doctor who gives remedies and dont recommend medicines {user_input}"
        response = chat_session.send_message(context)
        response_text = response.text

    context = {
        'response': response_text,
    }
    patient=models.Patient.objects.get(user_id=request.user.id)
    return render(request, 'chat_bot.html', context)


@login_required(login_url='patientlogin')
@user_passes_test(is_patient)
def patient_graph(request):
    patient=models.Patient.objects.get(user_id=request.user.id) 
    return render(request,'graph.html',{'patient':patient})


@login_required(login_url='patientlogin')
@user_passes_test(is_patient)
def one_on_onechat(request):
    patient=models.Patient.objects.get(user_id=request.user.id) 
    return render(request,'hospital/1-1_chat.html',{'patient':patient})


@login_required(login_url='doctor')
@user_passes_test(is_doctor)
def one_on_onechat_doctor(request):
    doctors=models.Doctor.objects.all().filter(status=True)
    return render(request,'hospital/1-1_chat_doctor.html',{'doctors':doctors})


@login_required(login_url='doctor')
@user_passes_test(is_doctor)
def upload_video(request):
    if request.method == 'POST':
        form = forms.VideoForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('doctor-dashboard')
    else:
        form =forms.VideoForm()
    return render(request, 'hospital/upload.html', {'form': form})


@login_required(login_url='patientlogin')
@user_passes_test(is_patient)
def patient_medtube(request):
    videos = models.Video.objects.all()
    return render(request, 'hospital/patient_medtube.html', {'videos': videos})

def manage_videos(request):
    videos = models.Video.objects.all()
    return render(request, 'hospital/manage.html', {'videos': videos})

def delete_video(request, video_id):
    video = models.Video.objects.get(id=video_id)
    video.delete()
    return redirect('admin-manage')


def publicgraph(request):
      return render(request,'hospital/publicgraph.html')


@login_required(login_url='doctor')
@user_passes_test(is_doctor)
def doctor_chat_view(request):
    patients=models.Patient.objects.all().filter(status=True)
    return render(request,'hospital/doctor_chat_view.html',{'patients':patients})


@login_required(login_url='patientlogin')
@user_passes_test(is_patient)
def patient_chat_view(request):
    doctors=models.Doctor.objects.all().filter(status=True)
    patient=models.Patient.objects.get(user_id=request.user.id) #for profile picture of patient in sidebar
    return render(request,'hospital/patient_chat_view.html',{'patient':patient,'doctors':doctors})


def search_doctor_reports_view(request):
    patient=models.Patient.objects.get(user_id=request.user.id) #for profile picture of patient in sidebar
    # whatever user write in search box we get in query
    query = request.GET['query']
    doctors=models.Doctor.objects.all().filter(status=True).filter(Q(department__icontains=query)| Q(user__first_name__icontains=query))
    return render(request,'hospital/patient_view_reports.html',{'patient':patient,'doctors':doctors})


def patient_reports(request):
    patient=models.Patient.objects.get(user_id=request.user.id)
    return render(request,'patient_reports.html',{'patient':patient})

def admin_patient_report_select(request,pk):
    patient=models.Patient.objects.get(id=pk)
    return render(request,'hospital/admin_patient_report_select.html',{'patient':patient})


@login_required(login_url='patientlogin')
@user_passes_test(is_patient)
def patient_reports_lipid(request):
    patient = get_object_or_404(models.Patient, user=request.user) #for profile picture of patient in sidebar
    reports = models.LipidProfile.objects.filter(patient=patient)
    return render(request,'hospital/patient_view_lipid_reports.html',{'reports':reports,'patient':patient})


@login_required(login_url='patientlogin')
@user_passes_test(is_patient)
def patient_reports_vitamin(request):
    patient = get_object_or_404(models.Patient, user=request.user) #for profile picture of patient in sidebar
    reports = models.Vitamin_Reports.objects.filter(patient=patient)
    return render(request,'hospital/patient_view_vitamin_reports.html',{'reports':reports,'patient':patient})


@login_required(login_url='patientlogin')
@user_passes_test(is_patient)
def patient_reports_ppbs(request):
    patient = get_object_or_404(models.Patient, user=request.user) #for profile picture of patient in sidebar
    reports = models.PPBS_Reports.objects.filter(patient=patient)
    return render(request,'hospital/patient_view_ppbs_reports.html',{'reports':reports,'patient':patient})


@login_required(login_url='patientlogin')
@user_passes_test(is_patient)
def patient_reports_fbs(request):
    patient = get_object_or_404(models.Patient, user=request.user) #for profile picture of patient in sidebar
    reports = models.FBS_Reports.objects.filter(patient=patient)
    return render(request,'hospital/patient_view_fbs_reports.html',{'reports':reports,'patient':patient})