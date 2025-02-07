# Generated by Django 5.0.7 on 2024-08-30 16:08

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hospital', '0026_lipidprofile_address_lipidprofile_admitdate_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='Vitamin_Reports',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('patientId', models.PositiveIntegerField(null=True)),
                ('assignedDoctorName', models.CharField(max_length=40)),
                ('address', models.CharField(max_length=40)),
                ('mobile', models.CharField(max_length=20, null=True)),
                ('symptoms', models.CharField(max_length=100, null=True)),
                ('admitDate', models.DateField()),
                ('todayDate', models.DateField()),
                ('FastingBloodSugar', models.CharField(max_length=40)),
                ('patient', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='hospital.patient')),
            ],
        ),
    ]
