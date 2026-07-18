"""Generate synthetic PDF documents for the industrial corpus."""

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.units import inch
import os

# Base path for output
BASE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "corpus")

def create_inspection_reports():
    """Create inspection report PDFs."""
    reports_path = os.path.join(BASE_PATH, "inspection_reports")
    os.makedirs(reports_path, exist_ok=True)

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        spaceAfter=12,
        textColor=colors.darkblue
    )
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=12,
        spaceBefore=12,
        spaceAfter=6
    )

    # Inspection Report 1: V-310 with CUI finding (PLANTED GAP - no work order addresses this)
    doc = SimpleDocTemplate(
        os.path.join(reports_path, "INS-2023-V310-001.pdf"),
        pagesize=letter
    )
    story = []
    story.append(Paragraph("VANTARA PETROCHEM - UNIT 3", title_style))
    story.append(Paragraph("PRESSURE VESSEL INSPECTION REPORT", styles['Heading2']))
    story.append(Spacer(1, 0.2*inch))

    info_data = [
        ["Report Number:", "INS-2023-V310-001"],
        ["Equipment Tag:", "V-310"],
        ["Equipment Type:", "Pressure Vessel - Overhead Accumulator Drum"],
        ["Inspection Date:", "2023-08-15"],
        ["Inspector:", "Arvind Menon (EMP-005)"],
        ["Inspection Type:", "External Visual + UT Thickness Survey"],
    ]
    info_table = Table(info_data, colWidths=[2*inch, 4*inch])
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 0.3*inch))

    story.append(Paragraph("THICKNESS SURVEY RESULTS", heading_style))
    thickness_data = [
        ["Location", "Nominal (mm)", "Measured (mm)", "% Loss", "Status"],
        ["Shell Course 1 - 0°", "12.0", "11.8", "1.7%", "ACCEPTABLE"],
        ["Shell Course 1 - 90°", "12.0", "11.7", "2.5%", "ACCEPTABLE"],
        ["Shell Course 1 - 180°", "12.0", "11.9", "0.8%", "ACCEPTABLE"],
        ["Shell Course 1 - 270°", "12.0", "11.6", "3.3%", "ACCEPTABLE"],
        ["Shell Course 2 - 0°", "12.0", "11.5", "4.2%", "ACCEPTABLE"],
        ["Shell Course 2 - 90°", "12.0", "10.2", "15.0%", "REQUIRES ACTION"],
        ["Shell Course 2 - 180°", "12.0", "11.4", "5.0%", "ACCEPTABLE"],
        ["Shell Course 2 - 270°", "12.0", "10.8", "10.0%", "MONITOR"],
        ["Head - Top", "14.0", "13.8", "1.4%", "ACCEPTABLE"],
        ["Head - Bottom", "14.0", "13.6", "2.9%", "ACCEPTABLE"],
    ]
    t = Table(thickness_data, colWidths=[1.8*inch, 1*inch, 1*inch, 0.8*inch, 1.2*inch])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BACKGROUND', (4, 6), (4, 6), colors.red),
        ('TEXTCOLOR', (4, 6), (4, 6), colors.white),
        ('BACKGROUND', (4, 8), (4, 8), colors.orange),
    ]))
    story.append(t)
    story.append(Spacer(1, 0.3*inch))

    story.append(Paragraph("FINDINGS AND OBSERVATIONS", heading_style))
    story.append(Paragraph("""
    <b>CRITICAL FINDING - CUI Detected:</b><br/>
    Location: Shell Course 2, 90° position (North side)<br/>
    Insulation was removed for inspection at suspected CUI location. Significant external corrosion
    observed under insulation. Wall thickness reduced to 10.2mm from nominal 12.0mm, representing
    15% wall loss. This exceeds the 10% threshold per OISD-STD-119 Section 5.1.4 requiring engineering
    assessment within 30 days.<br/><br/>

    <b>Root Cause Assessment:</b> Moisture ingress through damaged insulation jacket at pipe support
    location. Galvanic corrosion accelerated by dissimilar metal contact with carbon steel support clip.<br/><br/>

    <b>Secondary Finding:</b><br/>
    Location: Shell Course 2, 270° position<br/>
    Wall loss at 10% - at threshold level. Recommend monitoring at 6-month interval.
    """, styles['Normal']))
    story.append(Spacer(1, 0.2*inch))

    story.append(Paragraph("RECOMMENDATIONS", heading_style))
    story.append(Paragraph("""
    <b>IMMEDIATE (within 30 days):</b><br/>
    1. Engineering assessment required per OISD-STD-119 for 15% wall loss finding<br/>
    2. Repair or replace insulation jacket at affected location<br/>
    3. Install insulation standoff at pipe support to eliminate galvanic couple<br/>
    4. Consider protective coating application to affected area<br/><br/>

    <b>MONITORING:</b><br/>
    1. Re-inspect 270° location at 6-month interval<br/>
    2. Add V-310 to CUI susceptibility monitoring program<br/><br/>

    <b>Note:</b> Work order must be raised within 7 days per compliance requirements to initiate
    corrective action for critical finding.
    """, styles['Normal']))
    story.append(Spacer(1, 0.3*inch))

    story.append(Paragraph("CERTIFICATION", heading_style))
    story.append(Paragraph("""
    This inspection was performed in accordance with API 510 and company procedures.
    The equipment is fit for continued service provided the recommendations above are
    implemented within the specified timeframes.<br/><br/>

    Inspector: Arvind Menon, API 510 Certified<br/>
    Date: 2023-08-15<br/>
    Next Inspection Due: 2024-08-15 (or upon completion of repairs, whichever is earlier)
    """, styles['Normal']))

    doc.build(story)
    print("Created: INS-2023-V310-001.pdf (with CUI finding - PLANTED COMPLIANCE GAP)")

    # Inspection Report 2: E-205 Heat Exchanger
    doc = SimpleDocTemplate(
        os.path.join(reports_path, "INS-2023-E205-001.pdf"),
        pagesize=letter
    )
    story = []
    story.append(Paragraph("VANTARA PETROCHEM - UNIT 3", title_style))
    story.append(Paragraph("HEAT EXCHANGER INSPECTION REPORT", styles['Heading2']))
    story.append(Spacer(1, 0.2*inch))

    info_data = [
        ["Report Number:", "INS-2023-E205-001"],
        ["Equipment Tag:", "E-205"],
        ["Equipment Type:", "Shell-and-Tube Heat Exchanger"],
        ["Inspection Date:", "2023-06-20"],
        ["Inspector:", "Arvind Menon (EMP-005)"],
        ["Inspection Type:", "Internal + Tube Bundle Inspection"],
    ]
    info_table = Table(info_data, colWidths=[2*inch, 4*inch])
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 0.3*inch))

    story.append(Paragraph("INSPECTION FINDINGS", heading_style))
    story.append(Paragraph("""
    <b>Shell Side:</b><br/>
    - No significant corrosion observed<br/>
    - Baffles intact, no erosion at tube holes<br/>
    - Nozzle welds visually satisfactory<br/><br/>

    <b>Tube Bundle:</b><br/>
    - 3 tubes plugged during this inspection (tubes 45, 78, 112) due to external corrosion pitting<br/>
    - Estimated 5% tube area loss - acceptable for continued operation<br/>
    - Fouling deposits observed, chemical cleaning performed<br/><br/>

    <b>Channel/Tubesheet:</b><br/>
    - Tubesheet face in good condition<br/>
    - Gasket surfaces acceptable<br/>
    - Channel cover bolting satisfactory
    """, styles['Normal']))
    story.append(Spacer(1, 0.2*inch))

    story.append(Paragraph("RECOMMENDATIONS", heading_style))
    story.append(Paragraph("""
    1. Monitor heat transfer performance - efficiency may decrease with plugged tubes<br/>
    2. Consider tube bundle replacement during next turnaround if plugged tube count exceeds 10%<br/>
    3. Next inspection due in 24 months or at turnaround
    """, styles['Normal']))
    story.append(Spacer(1, 0.2*inch))

    story.append(Paragraph("CERTIFICATION", heading_style))
    story.append(Paragraph("""
    Equipment is FIT FOR SERVICE.<br/>
    Inspector: Arvind Menon<br/>
    Date: 2023-06-20
    """, styles['Normal']))

    doc.build(story)
    print("Created: INS-2023-E205-001.pdf")

    # Inspection Report 3: P-101A Vibration Analysis
    doc = SimpleDocTemplate(
        os.path.join(reports_path, "INS-2024-P101A-VIB-001.pdf"),
        pagesize=letter
    )
    story = []
    story.append(Paragraph("VANTARA PETROCHEM - UNIT 3", title_style))
    story.append(Paragraph("VIBRATION ANALYSIS REPORT", styles['Heading2']))
    story.append(Spacer(1, 0.2*inch))

    info_data = [
        ["Report Number:", "INS-2024-P101A-VIB-001"],
        ["Equipment Tag:", "P-101A"],
        ["Equipment Type:", "Centrifugal Pump"],
        ["Analysis Date:", "2024-02-15"],
        ["Analyst:", "Priya Sharma (EMP-002)"],
        ["Analysis Type:", "Routine Vibration Monitoring"],
    ]
    info_table = Table(info_data, colWidths=[2*inch, 4*inch])
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 0.3*inch))

    story.append(Paragraph("VIBRATION READINGS", heading_style))
    vib_data = [
        ["Measurement Point", "Velocity (mm/s)", "Alarm Level", "Status"],
        ["Pump DE Horizontal", "2.1", "4.5", "GOOD"],
        ["Pump DE Vertical", "1.8", "4.5", "GOOD"],
        ["Pump DE Axial", "1.2", "3.5", "GOOD"],
        ["Pump NDE Horizontal", "2.3", "4.5", "GOOD"],
        ["Pump NDE Vertical", "1.9", "4.5", "GOOD"],
        ["Motor DE Horizontal", "1.5", "4.5", "GOOD"],
        ["Motor DE Vertical", "1.3", "4.5", "GOOD"],
        ["Motor NDE Horizontal", "1.4", "4.5", "GOOD"],
        ["Motor NDE Vertical", "1.2", "4.5", "GOOD"],
    ]
    t = Table(vib_data, colWidths=[2*inch, 1.2*inch, 1*inch, 1*inch])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
    ]))
    story.append(t)
    story.append(Spacer(1, 0.2*inch))

    story.append(Paragraph("ANALYSIS NOTES", heading_style))
    story.append(Paragraph("""
    All vibration levels within acceptable limits. No indication of bearing wear,
    misalignment, or imbalance. Pump operating normally following seal replacement
    in January 2024 (WO-2024-001). Running on approved VantaLube Premium 320 lubricant.<br/><br/>

    Continue routine monthly monitoring. No action required.
    """, styles['Normal']))

    doc.build(story)
    print("Created: INS-2024-P101A-VIB-001.pdf")

    # Inspection Report 4: PSV-301 Testing
    doc = SimpleDocTemplate(
        os.path.join(reports_path, "INS-2023-PSV301-001.pdf"),
        pagesize=letter
    )
    story = []
    story.append(Paragraph("VANTARA PETROCHEM - UNIT 3", title_style))
    story.append(Paragraph("PRESSURE SAFETY VALVE TEST REPORT", styles['Heading2']))
    story.append(Spacer(1, 0.2*inch))

    info_data = [
        ["Report Number:", "INS-2023-PSV301-001"],
        ["Equipment Tag:", "PSV-301"],
        ["Protected Equipment:", "V-310 Pressure Vessel"],
        ["Test Date:", "2023-08-05"],
        ["Tester:", "Arvind Menon (EMP-005)"],
        ["Test Type:", "Annual PSV Verification - Bench Test"],
    ]
    info_table = Table(info_data, colWidths=[2*inch, 4*inch])
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 0.3*inch))

    story.append(Paragraph("TEST RESULTS", heading_style))
    test_data = [
        ["Parameter", "Nameplate", "As Found", "As Left", "Tolerance"],
        ["Set Pressure (bar)", "13.2", "13.4", "13.2", "+/- 3%"],
        ["Blowdown (%)", "7%", "8%", "7%", "5-10%"],
        ["Seat Tightness", "No Leak", "Pass", "Pass", "API 527"],
    ]
    t = Table(test_data, colWidths=[1.5*inch, 1*inch, 1*inch, 1*inch, 1*inch])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
    ]))
    story.append(t)
    story.append(Spacer(1, 0.2*inch))

    story.append(Paragraph("CERTIFICATION", heading_style))
    story.append(Paragraph("""
    PSV-301 tested and certified per API 576 requirements.<br/>
    Valve adjusted and resealed. New lead seal applied.<br/>
    Certificate valid until: 2024-08-05<br/><br/>

    Certified By: Arvind Menon<br/>
    Reference: PESO Rules, Rule 14
    """, styles['Normal']))

    doc.build(story)
    print("Created: INS-2023-PSV301-001.pdf")

    # Inspection Report 5: T-401 Tank Inspection
    doc = SimpleDocTemplate(
        os.path.join(reports_path, "INS-2023-T401-001.pdf"),
        pagesize=letter
    )
    story = []
    story.append(Paragraph("VANTARA PETROCHEM - UNIT 3", title_style))
    story.append(Paragraph("STORAGE TANK INSPECTION REPORT", styles['Heading2']))
    story.append(Spacer(1, 0.2*inch))

    info_data = [
        ["Report Number:", "INS-2023-T401-001"],
        ["Equipment Tag:", "T-401"],
        ["Equipment Type:", "Intermediate Naphtha Storage Tank"],
        ["Inspection Date:", "2023-04-22"],
        ["Inspector:", "Arvind Menon (EMP-005)"],
        ["Inspection Type:", "Internal Inspection per API 653"],
    ]
    info_table = Table(info_data, colWidths=[2*inch, 4*inch])
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 0.3*inch))

    story.append(Paragraph("INSPECTION FINDINGS", heading_style))
    story.append(Paragraph("""
    <b>Floor Plates:</b><br/>
    - MFL scan completed, no significant wall loss detected<br/>
    - Minimum thickness 8.2mm (nominal 9.5mm) - acceptable<br/>
    - No underside corrosion indications<br/><br/>

    <b>Shell Plates:</b><br/>
    - UT thickness survey on all courses<br/>
    - All readings within acceptable limits<br/>
    - No pitting or localized corrosion observed<br/><br/>

    <b>Roof:</b><br/>
    - Floating roof in good condition<br/>
    - Rim seal intact<br/>
    - Drain system functional<br/><br/>

    <b>Appurtenances:</b><br/>
    - All nozzles satisfactory<br/>
    - Gauge hatch gasket replaced (minor wear noted)<br/>
    - Level instrument connections intact
    """, styles['Normal']))
    story.append(Spacer(1, 0.2*inch))

    story.append(Paragraph("CONCLUSION", heading_style))
    story.append(Paragraph("""
    Tank T-401 is FIT FOR SERVICE.<br/>
    Next internal inspection due: April 2025 (24-month interval per API 653)<br/><br/>

    Inspector: Arvind Menon, API 653 Certified<br/>
    Date: 2023-04-22
    """, styles['Normal']))

    doc.build(story)
    print("Created: INS-2023-T401-001.pdf")

    # Inspection Report 6: C-102 Compressor Inspection
    doc = SimpleDocTemplate(
        os.path.join(reports_path, "INS-2023-C102-001.pdf"),
        pagesize=letter
    )
    story = []
    story.append(Paragraph("VANTARA PETROCHEM - UNIT 3", title_style))
    story.append(Paragraph("COMPRESSOR INSPECTION REPORT", styles['Heading2']))
    story.append(Spacer(1, 0.2*inch))

    info_data = [
        ["Report Number:", "INS-2023-C102-001"],
        ["Equipment Tag:", "C-102"],
        ["Equipment Type:", "Reciprocating Compressor - H2 Recycle"],
        ["Inspection Date:", "2023-11-10"],
        ["Inspector:", "Rajesh Kumar (EMP-001) / Priya Sharma (EMP-002)"],
        ["Inspection Type:", "Annual Turnaround Inspection"],
    ]
    info_table = Table(info_data, colWidths=[2*inch, 4*inch])
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 0.3*inch))

    story.append(Paragraph("INSPECTION FINDINGS", heading_style))
    story.append(Paragraph("""
    <b>Cylinders:</b><br/>
    - Cylinder 1: Bore within tolerance, minor scoring - polished<br/>
    - Cylinder 2: Satisfactory condition<br/>
    - Cylinder 3: Packing replaced (WO-2024-003 scope)<br/><br/>

    <b>Valves:</b><br/>
    - All suction and discharge valves replaced per planned scope<br/>
    - Previous valves showed fatigue cracking (reference WO-2023-015)<br/><br/>

    <b>Piston/Rods:</b><br/>
    - Piston rod runout within limits<br/>
    - Rider bands replaced on all pistons<br/><br/>

    <b>Bearings/Crossheads:</b><br/>
    - Main bearings within tolerance<br/>
    - Crosshead pin bearings replaced<br/><br/>

    <b>Foundation:</b><br/>
    - All anchor bolts retorqued<br/>
    - Foundation grout inspected - no cracks<br/>
    - Reference: Previous vibration issue (INC-2023-011)
    """, styles['Normal']))
    story.append(Spacer(1, 0.2*inch))

    story.append(Paragraph("CERTIFICATION", heading_style))
    story.append(Paragraph("""
    Compressor C-102 restored to service following annual overhaul.<br/>
    Next major inspection due: November 2024<br/><br/>

    Inspectors: Rajesh Kumar, Priya Sharma<br/>
    Date: 2023-11-10
    """, styles['Normal']))

    doc.build(story)
    print("Created: INS-2023-C102-001.pdf")

    # Inspection Report 7: H-501 Fired Heater
    doc = SimpleDocTemplate(
        os.path.join(reports_path, "INS-2024-H501-001.pdf"),
        pagesize=letter
    )
    story = []
    story.append(Paragraph("VANTARA PETROCHEM - UNIT 3", title_style))
    story.append(Paragraph("FIRED HEATER INSPECTION REPORT", styles['Heading2']))
    story.append(Spacer(1, 0.2*inch))

    info_data = [
        ["Report Number:", "INS-2024-H501-001"],
        ["Equipment Tag:", "H-501"],
        ["Equipment Type:", "Crude Charge Heater"],
        ["Inspection Date:", "2024-01-20"],
        ["Inspector:", "Arvind Menon (EMP-005)"],
        ["Inspection Type:", "Tube Skin Temperature Survey + Visual"],
    ]
    info_table = Table(info_data, colWidths=[2*inch, 4*inch])
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 0.3*inch))

    story.append(Paragraph("INSPECTION FINDINGS", heading_style))
    story.append(Paragraph("""
    <b>Tube Condition:</b><br/>
    - Infrared thermography survey completed<br/>
    - Maximum tube skin temperature: 365°C (design limit: 380°C)<br/>
    - No hot spots detected following decoking (ref: WO-2023-019)<br/><br/>

    <b>Refractory:</b><br/>
    - Minor spalling in radiant section - localized repair completed<br/>
    - Convection section refractory satisfactory<br/><br/>

    <b>Burners:</b><br/>
    - All burners inspected - flame patterns acceptable<br/>
    - Burner tips cleaned during December 2023 maintenance
    """, styles['Normal']))
    story.append(Spacer(1, 0.2*inch))

    story.append(Paragraph("CERTIFICATION", heading_style))
    story.append(Paragraph("""
    H-501 is FIT FOR SERVICE.<br/>
    Next inspection: January 2025 or at turnaround<br/><br/>

    Inspector: Arvind Menon<br/>
    Date: 2024-01-20
    """, styles['Normal']))

    doc.build(story)
    print("Created: INS-2024-H501-001.pdf")

    # Inspection Report 8: D-601 Distillation Column
    doc = SimpleDocTemplate(
        os.path.join(reports_path, "INS-2024-D601-001.pdf"),
        pagesize=letter
    )
    story = []
    story.append(Paragraph("VANTARA PETROCHEM - UNIT 3", title_style))
    story.append(Paragraph("DISTILLATION COLUMN INSPECTION REPORT", styles['Heading2']))
    story.append(Spacer(1, 0.2*inch))

    info_data = [
        ["Report Number:", "INS-2024-D601-001"],
        ["Equipment Tag:", "D-601"],
        ["Equipment Type:", "Atmospheric Distillation Tower"],
        ["Inspection Date:", "2024-03-18"],
        ["Inspector:", "Arvind Menon (EMP-005) / Rajesh Kumar (EMP-001)"],
        ["Inspection Type:", "Turnaround Internal Inspection"],
    ]
    info_table = Table(info_data, colWidths=[2*inch, 4*inch])
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 0.3*inch))

    story.append(Paragraph("INSPECTION FINDINGS", heading_style))
    story.append(Paragraph("""
    <b>Shell/Heads:</b><br/>
    - UT thickness survey - all readings above minimum<br/>
    - No external corrosion under insulation detected<br/><br/>

    <b>Trays:</b><br/>
    - Trays 1-17: Satisfactory condition<br/>
    - Trays 18-22: Heavy fouling confirmed (ref: WO-2023-011 gamma scan)<br/>
    - Cleaning completed, bubble caps inspected<br/>
    - Trays 20, 21: 4 bubble caps replaced (damaged)<br/>
    - Trays 23-42: Satisfactory<br/><br/>

    <b>Downcomers:</b><br/>
    - All downcomers clear<br/>
    - Seal pans intact<br/><br/>

    <b>Nozzles/Manways:</b><br/>
    - All nozzle welds inspected - satisfactory<br/>
    - Manway gaskets replaced
    """, styles['Normal']))
    story.append(Spacer(1, 0.2*inch))

    story.append(Paragraph("CERTIFICATION", heading_style))
    story.append(Paragraph("""
    D-601 restored to service following turnaround inspection.<br/>
    Next internal inspection: March 2028 (4-year cycle per RBI)<br/><br/>

    Inspectors: Arvind Menon, Rajesh Kumar<br/>
    Date: 2024-03-18<br/>
    Reference Work Order: WO-2024-005
    """, styles['Normal']))

    doc.build(story)
    print("Created: INS-2024-D601-001.pdf")


def create_sop_documents():
    """Create SOP PDF documents including one with a planted LOTO gap."""
    sop_path = os.path.join(BASE_PATH, "sops")
    os.makedirs(sop_path, exist_ok=True)

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        spaceAfter=12,
        textColor=colors.darkblue
    )

    # SOP 1: LOTO Procedure (PLANTED GAP - missing zero energy verification step)
    doc = SimpleDocTemplate(
        os.path.join(sop_path, "SOP-LOTO-001.pdf"),
        pagesize=letter
    )
    story = []
    story.append(Paragraph("VANTARA PETROCHEM - UNIT 3", title_style))
    story.append(Paragraph("STANDARD OPERATING PROCEDURE", styles['Heading2']))
    story.append(Paragraph("LOCKOUT-TAGOUT (LOTO) PROCEDURE", styles['Heading3']))
    story.append(Spacer(1, 0.2*inch))

    info_data = [
        ["Document Number:", "SOP-LOTO-001"],
        ["Revision:", "Rev 2"],
        ["Effective Date:", "2022-06-15"],
        ["Review Date:", "2024-06-15"],
        ["Author:", "Kavitha Reddy, HSE"],
        ["Approved By:", "Plant Manager"],
    ]
    info_table = Table(info_data, colWidths=[1.5*inch, 4*inch])
    info_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 0.3*inch))

    story.append(Paragraph("<b>1. PURPOSE</b>", styles['Heading3']))
    story.append(Paragraph("""
    This procedure establishes requirements for the lockout and tagout of energy
    isolating devices to prevent injury to personnel during maintenance activities.
    """, styles['Normal']))
    story.append(Spacer(1, 0.1*inch))

    story.append(Paragraph("<b>2. SCOPE</b>", styles['Heading3']))
    story.append(Paragraph("""
    Applies to all maintenance activities on rotating equipment, pressure systems,
    electrical systems, and any equipment with potential stored energy.
    """, styles['Normal']))
    story.append(Spacer(1, 0.1*inch))

    story.append(Paragraph("<b>3. PROCEDURE</b>", styles['Heading3']))
    story.append(Paragraph("""
    <b>3.1 Preparation</b><br/>
    - Identify all energy sources for the equipment<br/>
    - Notify affected personnel of impending shutdown<br/>
    - Obtain LOTO equipment (locks, tags, chains, blocks)<br/><br/>

    <b>3.2 Equipment Shutdown</b><br/>
    - Shut down equipment using normal operating procedures<br/>
    - Operate the energy isolating devices to isolate equipment from energy sources<br/><br/>

    <b>3.3 Lockout/Tagout Application</b><br/>
    - Apply locks to each energy isolating device<br/>
    - Apply tags indicating the equipment is locked out<br/>
    - Each worker applies their own personal lock<br/><br/>

    <b>3.4 Stored Energy Release</b><br/>
    - Release any stored energy (hydraulic, pneumatic, spring, gravitational)<br/>
    - Block or support equipment as necessary<br/><br/>

    <b>3.5 Perform Maintenance Work</b><br/>
    - Proceed with maintenance activities<br/>
    - Keep all LOTO devices in place until work is complete<br/><br/>

    <b>3.6 Restoration</b><br/>
    - Verify all tools and personnel are clear<br/>
    - Remove each person's lock in reverse order of application<br/>
    - Notify affected personnel before energizing
    """, styles['Normal']))
    # NOTE: PLANTED GAP - Missing the IS 14489:2018 Clause 6.2.3 required step:
    # "Verify zero energy state by attempting equipment startup before maintenance commences"
    story.append(Spacer(1, 0.2*inch))

    story.append(Paragraph("<b>4. REFERENCES</b>", styles['Heading3']))
    story.append(Paragraph("""
    - OSHA 29 CFR 1910.147<br/>
    - IS 14489:2018 (Lockout-Tagout Procedures)
    """, styles['Normal']))

    doc.build(story)
    print("Created: SOP-LOTO-001.pdf (PLANTED GAP - missing zero energy verification)")

    # SOP 2: Pump Startup Procedure
    doc = SimpleDocTemplate(
        os.path.join(sop_path, "SOP-PUMP-001.pdf"),
        pagesize=letter
    )
    story = []
    story.append(Paragraph("VANTARA PETROCHEM - UNIT 3", title_style))
    story.append(Paragraph("STANDARD OPERATING PROCEDURE", styles['Heading2']))
    story.append(Paragraph("CENTRIFUGAL PUMP STARTUP", styles['Heading3']))
    story.append(Spacer(1, 0.2*inch))

    info_data = [
        ["Document Number:", "SOP-PUMP-001"],
        ["Revision:", "Rev 3"],
        ["Effective Date:", "2023-03-01"],
        ["Applies To:", "P-101A, P-101B, and similar centrifugal pumps"],
        ["Author:", "Priya Sharma, Rotating Equipment"],
    ]
    info_table = Table(info_data, colWidths=[1.5*inch, 4*inch])
    info_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 0.3*inch))

    story.append(Paragraph("<b>STARTUP SEQUENCE</b>", styles['Heading3']))
    story.append(Paragraph("""
    <b>Pre-Start Checks:</b><br/>
    1. Verify LOTO removed and equipment is cleared for operation<br/>
    2. Check lubricant oil level in bearing housing - must be at center of sight glass<br/>
    3. Verify suction and discharge valves are in correct position<br/>
    4. Ensure minimum flow recirculation valve is functional<br/>
    5. Check seal flush system is operational<br/><br/>

    <b>Startup:</b><br/>
    1. Open suction valve fully<br/>
    2. Partially open discharge valve (to minimum flow position)<br/>
    3. Start pump motor<br/>
    4. Verify pump comes up to speed normally<br/>
    5. Check for unusual noise or vibration<br/>
    6. Slowly open discharge valve to operating position<br/>
    7. Monitor discharge pressure and flow<br/>
    8. Check bearing temperature (should stabilize within 30 minutes)<br/>
    9. Verify no leakage from mechanical seal<br/><br/>

    <b>Post-Start Monitoring:</b><br/>
    - First hour: Check every 15 minutes<br/>
    - After stabilization: Hourly checks per operator rounds<br/><br/>

    <b>IMPORTANT - Lubricant Requirements:</b><br/>
    Use ONLY approved lubricants as listed in equipment records. For P-101A/B,
    the approved lubricant is VantaLube Premium 320. Do not substitute without
    engineering approval and Management of Change review.
    """, styles['Normal']))

    doc.build(story)
    print("Created: SOP-PUMP-001.pdf")

    # SOP 3: Hot Work Permit Procedure
    doc = SimpleDocTemplate(
        os.path.join(sop_path, "SOP-HW-001.pdf"),
        pagesize=letter
    )
    story = []
    story.append(Paragraph("VANTARA PETROCHEM - UNIT 3", title_style))
    story.append(Paragraph("STANDARD OPERATING PROCEDURE", styles['Heading2']))
    story.append(Paragraph("HOT WORK PERMIT PROCEDURE", styles['Heading3']))
    story.append(Spacer(1, 0.2*inch))

    info_data = [
        ["Document Number:", "SOP-HW-001"],
        ["Revision:", "Rev 4"],
        ["Effective Date:", "2023-09-01"],
        ["Author:", "Kavitha Reddy, HSE"],
        ["Regulatory Reference:", "OISD-GDN-206"],
    ]
    info_table = Table(info_data, colWidths=[1.5*inch, 4*inch])
    info_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 0.3*inch))

    story.append(Paragraph("<b>PROCEDURE</b>", styles['Heading3']))
    story.append(Paragraph("""
    <b>1. Pre-Work Requirements:</b><br/>
    - Gas testing by certified gas tester (LEL must be &lt; 1%)<br/>
    - Fire extinguisher positioned within 10 meters<br/>
    - Fire blanket to cover drains and openings<br/>
    - Fire watch designated and briefed<br/><br/>

    <b>2. Permit Issuance:</b><br/>
    - Area supervisor issues hot work permit<br/>
    - Permit valid for single shift only<br/>
    - Continuous gas monitoring required<br/><br/>

    <b>3. During Hot Work:</b><br/>
    - Fire watch maintains continuous observation<br/>
    - Gas testing every 30 minutes<br/>
    - Work stops immediately if LEL exceeds 10%<br/><br/>

    <b>4. After Hot Work Completion:</b><br/>
    - Fire watch must remain on station for minimum 30 minutes after completion
      of hot work per OISD-GDN-206 Section 3.4<br/>
    - Final area inspection before fire watch release<br/>
    - Permit closed out and returned to control room
    """, styles['Normal']))

    doc.build(story)
    print("Created: SOP-HW-001.pdf")

    # SOP 4: Permit to Work System
    doc = SimpleDocTemplate(
        os.path.join(sop_path, "SOP-PTW-001.pdf"),
        pagesize=letter
    )
    story = []
    story.append(Paragraph("VANTARA PETROCHEM - UNIT 3", title_style))
    story.append(Paragraph("STANDARD OPERATING PROCEDURE", styles['Heading2']))
    story.append(Paragraph("PERMIT TO WORK SYSTEM", styles['Heading3']))
    story.append(Spacer(1, 0.2*inch))

    story.append(Paragraph("""
    <b>1. PERMIT TYPES</b><br/>
    - Cold Work Permit<br/>
    - Hot Work Permit (see SOP-HW-001)<br/>
    - Confined Space Entry Permit<br/>
    - Excavation Permit<br/>
    - Electrical Work Permit<br/><br/>

    <b>2. PERMIT PROCESS</b><br/>
    - Job Safety Analysis (JSA) completed<br/>
    - Area made safe per permit requirements<br/>
    - Permit issued by authorized issuer<br/>
    - Work performed within permit conditions<br/>
    - Permit closed upon completion<br/><br/>

    <b>3. PERMIT VALIDITY</b><br/>
    - Single shift or 12 hours maximum<br/>
    - Revalidation required for extended work<br/>
    - Permit void if conditions change
    """, styles['Normal']))

    doc.build(story)
    print("Created: SOP-PTW-001.pdf")

    # SOP 5: Emergency Shutdown Procedure
    doc = SimpleDocTemplate(
        os.path.join(sop_path, "SOP-ESD-001.pdf"),
        pagesize=letter
    )
    story = []
    story.append(Paragraph("VANTARA PETROCHEM - UNIT 3", title_style))
    story.append(Paragraph("STANDARD OPERATING PROCEDURE", styles['Heading2']))
    story.append(Paragraph("EMERGENCY SHUTDOWN PROCEDURE", styles['Heading3']))
    story.append(Spacer(1, 0.2*inch))

    info_data = [
        ["Document Number:", "SOP-ESD-001"],
        ["Revision:", "Rev 2"],
        ["Effective Date:", "2023-01-15"],
        ["Classification:", "CRITICAL"],
    ]
    info_table = Table(info_data, colWidths=[1.5*inch, 4*inch])
    info_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 0.3*inch))

    story.append(Paragraph("""
    <b>EMERGENCY SHUTDOWN TRIGGERS</b><br/>
    - Major hydrocarbon leak<br/>
    - Fire or explosion<br/>
    - Loss of utilities (steam, air, power)<br/>
    - High-high pressure or temperature alarms<br/>
    - Toxic gas release<br/><br/>

    <b>ESD ACTIONS</b><br/>
    <b>Level 1 - Equipment ESD:</b><br/>
    - Trips individual equipment (pump, compressor, heater)<br/>
    - Operator can initiate from field or control room<br/><br/>

    <b>Level 2 - Unit ESD:</b><br/>
    - Trips entire CDU unit<br/>
    - Closes all feed valves<br/>
    - Trips all fired equipment<br/>
    - Depressures to flare<br/><br/>

    <b>Level 3 - Plant ESD:</b><br/>
    - Full plant emergency shutdown<br/>
    - Initiated only by Shift Supervisor or Plant Manager<br/><br/>

    <b>POST-ESD ACTIONS</b><br/>
    - Account for all personnel<br/>
    - Assess situation before any restart<br/>
    - Document incident per INC procedure
    """, styles['Normal']))

    doc.build(story)
    print("Created: SOP-ESD-001.pdf")

    # SOP 6: Vessel Entry Procedure
    doc = SimpleDocTemplate(
        os.path.join(sop_path, "SOP-CSE-001.pdf"),
        pagesize=letter
    )
    story = []
    story.append(Paragraph("VANTARA PETROCHEM - UNIT 3", title_style))
    story.append(Paragraph("STANDARD OPERATING PROCEDURE", styles['Heading2']))
    story.append(Paragraph("CONFINED SPACE ENTRY PROCEDURE", styles['Heading3']))
    story.append(Spacer(1, 0.2*inch))

    info_data = [
        ["Document Number:", "SOP-CSE-001"],
        ["Revision:", "Rev 3"],
        ["Effective Date:", "2023-05-01"],
        ["Applies To:", "V-310, T-401, T-402, D-601 and similar vessels"],
    ]
    info_table = Table(info_data, colWidths=[1.5*inch, 4*inch])
    info_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 0.3*inch))

    story.append(Paragraph("""
    <b>PRE-ENTRY REQUIREMENTS</b><br/>
    - Vessel isolated, drained, and purged<br/>
    - LOTO applied per SOP-LOTO-001<br/>
    - Atmospheric testing (O2 19.5-23.5%, LEL &lt; 1%, H2S &lt; 5 ppm)<br/>
    - Entry permit issued<br/>
    - Rescue plan in place<br/>
    - Attendant stationed at entry point<br/><br/>

    <b>ENTRY PROCEDURE</b><br/>
    - Continuous atmospheric monitoring<br/>
    - Communication check every 15 minutes<br/>
    - Maximum entry duration: 2 hours continuous<br/><br/>

    <b>EMERGENCY RESCUE</b><br/>
    - Do NOT enter to rescue without SCBA<br/>
    - Use retrieval system if available<br/>
    - Call emergency response team
    """, styles['Normal']))

    doc.build(story)
    print("Created: SOP-CSE-001.pdf")


def create_pid_diagram():
    """Create a simple P&ID diagram as PNG."""
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    from matplotlib.patches import FancyBboxPatch, Circle

    pid_path = os.path.join(BASE_PATH, "diagrams")
    os.makedirs(pid_path, exist_ok=True)

    fig, ax = plt.subplots(1, 1, figsize=(16, 10))
    ax.set_xlim(0, 16)
    ax.set_ylim(0, 10)
    ax.set_aspect('equal')
    ax.axis('off')

    # Title
    ax.text(8, 9.5, 'VANTARA PETROCHEM - UNIT 3 CDU SIMPLIFIED P&ID',
            ha='center', fontsize=14, fontweight='bold')

    # Equipment shapes and labels
    # T-401 Tank (left)
    tank1 = FancyBboxPatch((0.5, 3), 1.5, 3, boxstyle="round,pad=0.1",
                            facecolor='lightblue', edgecolor='black', linewidth=2)
    ax.add_patch(tank1)
    ax.text(1.25, 4.5, 'T-401\nNaphtha\nTank', ha='center', va='center', fontsize=8, fontweight='bold')

    # P-101A Pump
    pump_circle = Circle((3.5, 3.5), 0.5, facecolor='lightgreen', edgecolor='black', linewidth=2)
    ax.add_patch(pump_circle)
    ax.text(3.5, 3.5, 'P-101A', ha='center', va='center', fontsize=7, fontweight='bold')
    ax.text(3.5, 2.7, 'Feed Pump', ha='center', fontsize=6)

    # P-101B Pump (standby)
    pump_circle2 = Circle((3.5, 5.5), 0.5, facecolor='lightyellow', edgecolor='black', linewidth=2)
    ax.add_patch(pump_circle2)
    ax.text(3.5, 5.5, 'P-101B', ha='center', va='center', fontsize=7, fontweight='bold')
    ax.text(3.5, 4.8, '(Standby)', ha='center', fontsize=6)

    # E-205 Heat Exchanger
    hx = FancyBboxPatch((5, 3.5), 1.5, 2, boxstyle="round,pad=0.05",
                         facecolor='lightyellow', edgecolor='black', linewidth=2)
    ax.add_patch(hx)
    ax.text(5.75, 4.5, 'E-205\nPreheater', ha='center', va='center', fontsize=8, fontweight='bold')

    # H-501 Fired Heater
    heater = FancyBboxPatch((7.5, 3), 1.5, 3, boxstyle="round,pad=0.1",
                             facecolor='lightsalmon', edgecolor='black', linewidth=2)
    ax.add_patch(heater)
    ax.text(8.25, 4.5, 'H-501\nCharge\nHeater', ha='center', va='center', fontsize=8, fontweight='bold')

    # D-601 Distillation Column (tall rectangle)
    column = FancyBboxPatch((10, 1), 1.5, 7, boxstyle="round,pad=0.1",
                             facecolor='lightgray', edgecolor='black', linewidth=2)
    ax.add_patch(column)
    ax.text(10.75, 4.5, 'D-601\nAtmospheric\nDistillation\nColumn', ha='center', va='center', fontsize=8, fontweight='bold')

    # V-310 Overhead Drum
    drum = FancyBboxPatch((12.5, 6), 2, 1.5, boxstyle="round,pad=0.1",
                           facecolor='lightcyan', edgecolor='black', linewidth=2)
    ax.add_patch(drum)
    ax.text(13.5, 6.75, 'V-310\nOverhead Drum', ha='center', va='center', fontsize=8, fontweight='bold')

    # PSV-301 (on V-310)
    ax.annotate('PSV-301', xy=(14.5, 7.5), fontsize=7, ha='center',
                bbox=dict(boxstyle='round', facecolor='red', alpha=0.3))
    ax.plot([14, 14.5], [7.5, 7.5], 'k-', linewidth=1)
    ax.plot([14, 14], [7.5, 7.0], 'k-', linewidth=1)

    # AG-701 Air Cooler
    cooler = FancyBboxPatch((12.5, 3.5), 2, 1.5, boxstyle="round,pad=0.1",
                             facecolor='lightsteelblue', edgecolor='black', linewidth=2)
    ax.add_patch(cooler)
    ax.text(13.5, 4.25, 'AG-701\nAir Cooler', ha='center', va='center', fontsize=8, fontweight='bold')

    # C-102 Compressor (offgas)
    comp = Circle((14.5, 2), 0.6, facecolor='plum', edgecolor='black', linewidth=2)
    ax.add_patch(comp)
    ax.text(14.5, 2, 'C-102', ha='center', va='center', fontsize=7, fontweight='bold')
    ax.text(14.5, 1.2, 'H2 Recycle\nCompressor', ha='center', fontsize=6)

    # T-402 Product Tank
    tank2 = FancyBboxPatch((12.5, 0.5), 1.5, 2, boxstyle="round,pad=0.1",
                            facecolor='lightblue', edgecolor='black', linewidth=2)
    ax.add_patch(tank2)
    ax.text(13.25, 1.5, 'T-402\nDiesel', ha='center', va='center', fontsize=8, fontweight='bold')

    # FV-1001 Control Valve
    ax.plot([4.2, 4.8], [3.5, 3.5], 'k-', linewidth=2)
    ax.annotate('FV-1001', xy=(4.5, 3.0), fontsize=7, ha='center',
                bbox=dict(boxstyle='round', facecolor='white'))

    # Process lines
    # T-401 to P-101A
    ax.annotate('', xy=(3.0, 3.5), xytext=(2.0, 4.5),
                arrowprops=dict(arrowstyle='->', color='blue', lw=2))

    # P-101A to E-205
    ax.annotate('', xy=(5.0, 4.5), xytext=(4.0, 3.5),
                arrowprops=dict(arrowstyle='->', color='blue', lw=2))

    # E-205 to H-501
    ax.annotate('', xy=(7.5, 4.5), xytext=(6.5, 4.5),
                arrowprops=dict(arrowstyle='->', color='blue', lw=2))

    # H-501 to D-601
    ax.annotate('', xy=(10.0, 4.5), xytext=(9.0, 4.5),
                arrowprops=dict(arrowstyle='->', color='blue', lw=2))

    # D-601 overhead to V-310
    ax.annotate('', xy=(12.5, 6.75), xytext=(11.5, 7.5),
                arrowprops=dict(arrowstyle='->', color='red', lw=2))

    # V-310 to AG-701
    ax.annotate('', xy=(13.5, 5.0), xytext=(13.5, 6.0),
                arrowprops=dict(arrowstyle='->', color='blue', lw=2))

    # D-601 side draw to T-402
    ax.annotate('', xy=(12.5, 1.5), xytext=(11.5, 3.0),
                arrowprops=dict(arrowstyle='->', color='green', lw=2))

    # Legend
    ax.text(0.5, 1.5, 'LEGEND:', fontsize=9, fontweight='bold')
    ax.text(0.5, 1.0, '→ Process Flow', fontsize=8, color='blue')
    ax.text(0.5, 0.6, '○ Pump/Compressor', fontsize=8)
    ax.text(0.5, 0.2, '□ Vessel/Column', fontsize=8)

    plt.tight_layout()
    plt.savefig(os.path.join(pid_path, 'CDU-PID-001.png'), dpi=150, bbox_inches='tight',
                facecolor='white', edgecolor='none')
    plt.close()
    print("Created: CDU-PID-001.png")


if __name__ == "__main__":
    print("Generating synthetic PDF documents...\n")
    create_inspection_reports()
    print()
    create_sop_documents()
    print()
    create_pid_diagram()
    print("\nAll documents generated successfully!")
