from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

def create_medical_pdf(filename, patient_name, condition, notes):
    c = canvas.Canvas(filename, pagesize=letter)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, 750, "AuraHealth Medical Consultation Report")
    c.setFont("Helvetica", 12)
    c.drawString(50, 700, f"Patient Name: {patient_name}")
    c.drawString(50, 680, f"Diagnosis: {condition}")
    c.drawString(50, 650, "Doctor Notes:")
    c.drawString(50, 630, notes)
    c.drawString(50, 610, "Patient was advised to monitor symptoms and follow up.")
    c.drawString(50, 590, "Prescribed standard medication regimen.")
    c.save()

create_medical_pdf("john_doe_cardiology_report.pdf", "John Doe", "Mild Arrhythmia", "Patient reported occasional palpitations. EKG shows minor irregularities.")
create_medical_pdf("jane_smith_post_op.pdf", "Jane Smith", "Post-Op Knee Surgery", "Incision healing well. Patient needs to continue physical therapy exercises.")
