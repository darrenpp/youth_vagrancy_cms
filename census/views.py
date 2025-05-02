from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from .models import CensusRecord
from django.db.models import Count
from django.utils import timezone
import json
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from datetime import datetime
import os
from django.conf import settings


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, 'Logged in successfully.')
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password.')
    return render(request, 'login.html')


def logout_view(request):
    logout(request)
    messages.success(request, 'Logged out successfully.')
    return redirect('login')


@login_required
def dashboard(request):
    # Paginate records to improve performance
    records = CensusRecord.objects.all().order_by('-date_recorded')
    paginator = Paginator(records, 10)  # Show 10 records per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'dashboard.html', {'records': page_obj})


@login_required
def add_record(request):
    if request.method == 'POST':
        try:
            name = request.POST.get('name')
            age = request.POST.get('age')
            gender = request.POST.get('gender')
            electorate = request.POST.get('electorate')
            reason = request.POST.get('reason')
            date_recorded = request.POST.get('date_recorded')
            image = request.FILES.get('image')

            # Validate inputs
            if not name or len(name) > 255:
                raise ValidationError('Invalid name.')
            if not age or not age.isdigit() or int(age) < 0:
                raise ValidationError('Invalid age.')
            if gender not in [choice[0] for choice in CensusRecord.GENDER_CHOICES]:
                raise ValidationError('Invalid gender.')
            if electorate not in [choice[0] for choice in CensusRecord.ELECTORATE_CHOICES]:
                raise ValidationError('Invalid electorate.')
            if not reason:
                raise ValidationError('Reason is required.')
            if not date_recorded:
                raise ValidationError('Date recorded is required.')

            # Validate image
            if image:
                if image.size > 5 * 1024 * 1024:  # Limit to 5MB
                    raise ValidationError('Image file too large.')
                if not image.content_type.startswith('image/'):
                    raise ValidationError('Invalid image format.')

            CensusRecord.objects.create(
                name=name,
                age=int(age),
                gender=gender,
                electorate=electorate,
                reason=reason,
                date_recorded=date_recorded,
                image=image
            )
            messages.success(request, 'Record added successfully.')
            return redirect('dashboard')
        except ValidationError as e:
            messages.error(request, f'Error adding record: {str(e)}')
        except Exception as e:
            messages.error(request, 'An unexpected error occurred. Please try again.')

    return render(request, 'add_record.html')


@login_required
def edit_record(request, id):
    record = get_object_or_404(CensusRecord, id=id)

    if request.method == 'POST':
        try:
            record.name = request.POST.get('name')
            record.age = request.POST.get('age')
            record.gender = request.POST.get('gender')
            record.electorate = request.POST.get('electorate')
            record.reason = request.POST.get('reason')
            record.date_recorded = request.POST.get('date_recorded')
            new_image = request.FILES.get('image')

            # Validate inputs
            if not record.name or len(record.name) > 255:
                raise ValidationError('Invalid name.')
            if not record.age or not str(record.age).isdigit() or int(record.age) < 0:
                raise ValidationError('Invalid age.')
            if record.gender not in [choice[0] for choice in CensusRecord.GENDER_CHOICES]:
                raise ValidationError('Invalid gender.')
            if record.electorate not in [choice[0] for choice in CensusRecord.ELECTORATE_CHOICES]:
                raise ValidationError('Invalid electorate.')
            if not record.reason:
                raise ValidationError('Reason is required.')
            if not record.date_recorded:
                raise ValidationError('Date recorded is required.')

            # Handle image update
            if new_image:
                if new_image.size > 5 * 1024 * 1024:  # Limit to 5MB
                    raise ValidationError('Image file too large.')
                if not new_image.content_type.startswith('image/'):
                    raise ValidationError('Invalid image format.')
                # Delete old image if it exists
                if record.image and os.path.isfile(record.image.path):
                    os.remove(record.image.path)
                record.image = new_image

            record.save()
            messages.success(request, 'Record updated successfully.')
            return redirect('dashboard')
        except ValidationError as e:
            messages.error(request, f'Error updating record: {str(e)}')
        except Exception as e:
            messages.error(request, 'An unexpected error occurred. Please try again.')

    return render(request, 'edit_record.html', {'record': record})


@login_required
def delete_record(request, id):
    try:
        record = get_object_or_404(CensusRecord, id=id)
        # Delete associated image file
        if record.image and os.path.isfile(record.image.path):
            os.remove(record.image.path)
        record.delete()
        messages.success(request, 'Record deleted successfully.')
    except Exception as e:
        messages.error(request, 'Error deleting record. Please try again.')
    return redirect('dashboard')


@login_required
def statistics(request):
    try:
        # Fetch electorate data
        electorate_data = CensusRecord.objects.values('electorate').annotate(count=Count('electorate'))
        electorate_labels = [item['electorate'] for item in electorate_data]
        electorate_counts = [item['count'] for item in electorate_data]

        # Fetch age distribution
        age_bins = [0, 18, 25, 35, 50, 100]
        age_labels = ['0-18', '19-25', '26-35', '36-50', '51+']
        age_counts = []
        for i in range(len(age_bins) - 1):
            count = CensusRecord.objects.filter(age__gte=age_bins[i], age__lt=age_bins[i + 1]).count()
            age_counts.append(count)

        # Map coordinates with fallback
        electorate_coords = {
            'Moresby South': [-9.478, 147.148],
            'Moresby Northeast': [-9.467, 147.183],
            'Moresby Northwest': [-9.443, 147.138],
            'Motukoitabu': [-9.483, 147.128],
        }
        map_data = []
        for item in electorate_data:
            coords = electorate_coords.get(item['electorate'], [-9.465, 147.155])  # Default to Port Moresby center
            map_data.append({
                'electorate': item['electorate'],
                'count': item['count'],
                'coords': coords
            })

        context = {
            'electorate_labels': json.dumps(electorate_labels),
            'electorate_counts': json.dumps(electorate_counts),
            'age_labels': json.dumps(age_labels),
            'age_counts': json.dumps(age_counts),
            'map_data': json.dumps(map_data),
        }
        return render(request, 'statistics.html', context)
    except Exception as e:
        messages.error(request, 'Error generating statistics. Please try again.')
        return render(request, 'statistics.html', {})


@login_required
def export_excel(request):
    try:
        records = CensusRecord.objects.all()
        data = [{
            'ID': record.id,
            'Name': record.name,
            'Age': record.age,
            'Gender': record.gender,
            'Electorate': record.electorate,
            'Reason': record.reason,
            'Date Recorded': record.date_recorded,
            'Image': str(record.image) if record.image else ''
        } for record in records]

        df = pd.DataFrame(data)
        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename="census_records.xlsx"'
        df.to_excel(response, index=False, engine='openpyxl')
        return response
    except Exception as e:
        messages.error(request, 'Error exporting to Excel. Please try again.')
        return redirect('dashboard')


@login_required
def export_pdf(request):
    try:
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="census_records.pdf"'

        doc = SimpleDocTemplate(response, pagesize=letter)
        elements = []

        records = CensusRecord.objects.all()
        data = [['ID', 'Name', 'Age', 'Gender', 'Electorate', 'Reason', 'Date Recorded', 'Image']]
        for record in records:
            reason = record.reason[:100] + '...' if len(record.reason) > 100 else record.reason  # Increased limit
            data.append([
                record.id,
                record.name,
                record.age,
                record.gender,
                record.electorate,
                reason,
                str(record.date_recorded),
                str(record.image) if record.image else ''
            ])

        # Adjust table column widths
        table = Table(data, colWidths=[40, 80, 40, 60, 80, 120, 80, 80])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        elements.append(table)
        doc.build(elements)
        return response
    except Exception as e:
        messages.error(request, 'Error exporting to PDF. Please try again.')
        return redirect('dashboard')