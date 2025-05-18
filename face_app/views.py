import cv2
import face_recognition
import numpy as np
from django.shortcuts import render, redirect
from django.http import StreamingHttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from .models import Employee, Attendance
import json
from datetime import date

# Global variables for face recognition
known_face_encodings = []
known_face_names = []
known_face_ids = []

def load_known_faces():
    global known_face_encodings, known_face_names, known_face_ids
    known_face_encodings = []
    known_face_names = []
    known_face_ids = []
    
    employees = Employee.objects.all()
    for employee in employees:
        try:
            image = face_recognition.load_image_file(employee.photo.path)
            encoding = face_recognition.face_encodings(image)[0]
            known_face_encodings.append(encoding)
            known_face_names.append(employee.name)
            known_face_ids.append(employee.employee_id)
        except:
            continue

def index(request):
    return render(request, 'face_app/index.html')

def add_employee(request):
    if request.method == 'POST':
        name = request.POST['name']
        employee_id = request.POST['employee_id']
        photo = request.FILES['photo']
        
        employee = Employee.objects.create(
            name=name,
            employee_id=employee_id,
            photo=photo
        )
        
        # Reload known faces
        load_known_faces()
        
        messages.success(request, f'Employee {name} added successfully!')
        return redirect('index')
    
    return render(request, 'face_app/add_employee.html')

def attendance_view(request):
    return render(request, 'face_app/attendance.html')

def attendance_list(request):
    today_attendance = Attendance.objects.filter(date=date.today())
    employees = Employee.objects.all()
    return render(request, 'face_app/attendance_list.html', {
        'today_attendance': today_attendance,
        'employees': employees
    })

class VideoCamera:
    def __init__(self):
        self.video = cv2.VideoCapture(0)
        load_known_faces()
    
    def __del__(self):
        self.video.release()
    
    def get_frame(self):
        success, image = self.video.read()
        if not success:
            return None
        
        # Resize frame for faster processing
        small_frame = cv2.resize(image, (0, 0), fx=0.25, fy=0.25)
        rgb_small_frame = small_frame[:, :, ::-1]
        
        # Find faces
        face_locations = face_recognition.face_locations(rgb_small_frame)
        face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)
        
        for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
            # Scale back up face locations
            top *= 4
            right *= 4
            bottom *= 4
            left *= 4
            
            # Compare with known faces
            matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
            name = "Unknown"
            
            if True in matches:
                first_match_index = matches.index(True)
                name = known_face_names[first_match_index]
                emp_id = known_face_ids[first_match_index]
                
                # Mark attendance
                try:
                    employee = Employee.objects.get(employee_id=emp_id)
                    attendance, created = Attendance.objects.get_or_create(
                        employee=employee,
                        date=date.today()
                    )
                    if created:
                        print(f"Attendance marked for {name}")
                except:
                    pass
            
            # Draw rectangle and name
            cv2.rectangle(image, (left, top), (right, bottom), (0, 255, 0), 2)
            cv2.rectangle(image, (left, bottom - 35), (right, bottom), (0, 255, 0), cv2.FILLED)
            cv2.putText(image, name, (left + 6, bottom - 6), cv2.FONT_HERSHEY_DUPLEX, 0.6, (255, 255, 255), 1)
        
        ret, jpeg = cv2.imencode('.jpg', image)
        return jpeg.tobytes()

def gen(camera):
    while True:
        frame = camera.get_frame()
        if frame is not None:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')

def video_feed(request):
    return StreamingHttpResponse(gen(VideoCamera()),
                                content_type='multipart/x-mixed-replace; boundary=frame')