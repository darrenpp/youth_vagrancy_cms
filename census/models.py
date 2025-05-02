from django.db import models
from django.core.files.storage import FileSystemStorage

fs = FileSystemStorage(location='media/images/')

class CensusRecord(models.Model):
    objects = None
    GENDER_CHOICES = [
        ('Male', 'Male'),
        ('Female', 'Female'),
        ('Other', 'Other'),
    ]
    ELECTORATE_CHOICES = [
        ('Moresby South', 'Moresby South'),
        ('Moresby Northeast', 'Moresby Northeast'),
        ('Moresby Northwest', 'Moresby Northwest'),
        ('Motukoitabu', 'Motukoitabu'),
    ]

    name = models.CharField(max_length=255)
    age = models.PositiveIntegerField()
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    electorate = models.CharField(max_length=50, choices=ELECTORATE_CHOICES)
    reason = models.TextField()
    date_recorded = models.DateField()
    image = models.ImageField(upload_to='images/', storage=fs, blank=True, null=True)

    def __str__(self):
        return self.name