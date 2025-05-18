from django.db import models
from django.utils import timezone

class Employee(models.Model):
    name = models.CharField(max_length=100)
    employee_id = models.CharField(max_length=50, unique=True)
    photo = models.ImageField(upload_to='employee_photos/')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.name} ({self.employee_id})"

class Attendance(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    check_in_time = models.DateTimeField(default=timezone.now)
    date = models.DateField(auto_now_add=True)
    
    class Meta:
        unique_together = ['employee', 'date']
    
    def __str__(self):
        return f"{self.employee.name} - {self.date}"