"""Generate the lubrication standard PDF for the corpus."""

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.units import inch
import os

BASE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "corpus", "standards")
os.makedirs(BASE_PATH, exist_ok=True)

def create_lubrication_standard():
    """Create lubrication standard PDF with compatibility requirements."""

    doc = SimpleDocTemplate(
        os.path.join(BASE_PATH, "LUB-STD-001.pdf"),
        pagesize=letter
    )

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
    warning_style = ParagraphStyle(
        'Warning',
        parent=styles['Normal'],
        backColor=colors.lightyellow,
        borderColor=colors.red,
        borderWidth=1,
        borderPadding=5,
        spaceBefore=10,
        spaceAfter=10
    )

    story = []

    # Title
    story.append(Paragraph("VANTARA PETROCHEM - UNIT 3", title_style))
    story.append(Paragraph("LUBRICATION STANDARD", styles['Heading2']))
    story.append(Paragraph("Document Number: LUB-STD-001 | Revision: 3 | Effective: 2022-01-15", styles['Normal']))
    story.append(Spacer(1, 0.3*inch))

    # Scope
    story.append(Paragraph("1. SCOPE AND PURPOSE", heading_style))
    story.append(Paragraph("""
    This standard defines approved lubricants for rotating equipment at Vantara Petrochem Unit 3.
    All maintenance personnel shall follow these requirements when selecting lubricants for
    equipment lubrication, oil changes, and top-ups. Use of non-approved lubricants may void
    equipment warranties and cause premature component failure.
    """, styles['Normal']))
    story.append(Spacer(1, 0.2*inch))

    # Approved lubricants table
    story.append(Paragraph("2. APPROVED LUBRICANTS", heading_style))

    lub_data = [
        ["Stock Code", "Product Name", "Type", "Approved Applications"],
        ["LUB-001", "VantaLube Premium 320", "Mineral Oil (Group II)", "All rotating equipment including pumps, compressors, gearboxes"],
        ["LUB-002", "SynthMax HP 220", "Synthetic PAO", "High-temperature applications above 120°C"],
        ["LUB-003", "EconoLube Standard 320", "Mineral Oil (Group I)", "NON-CRITICAL equipment only - see Section 4 restrictions"],
    ]

    t = Table(lub_data, colWidths=[0.9*inch, 1.6*inch, 1.3*inch, 2.4*inch])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BACKGROUND', (0, 3), (-1, 3), colors.lightyellow),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(t)
    story.append(Spacer(1, 0.2*inch))

    # Equipment compatibility
    story.append(Paragraph("3. EQUIPMENT-SPECIFIC REQUIREMENTS", heading_style))

    equip_data = [
        ["Equipment Type", "Seal Type", "Required Lubricant", "Notes"],
        ["Centrifugal Pumps (Critical)", "FFKM/Fluorocarbon", "LUB-001 or LUB-002 ONLY", "Includes P-101A, P-101B"],
        ["Centrifugal Pumps (Non-critical)", "NBR/Nitrile", "LUB-001, LUB-002, or LUB-003", ""],
        ["Reciprocating Compressors", "PTFE Packing", "LUB-001 or LUB-002", "Includes C-102"],
        ["Gearboxes", "Lip Seals", "LUB-001, LUB-002, or LUB-003", ""],
    ]

    t = Table(equip_data, colWidths=[1.5*inch, 1.2*inch, 1.5*inch, 1.5*inch])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(t)
    story.append(Spacer(1, 0.3*inch))

    # Critical warning section
    story.append(Paragraph("4. LUBRICANT RESTRICTIONS - CRITICAL", heading_style))
    story.append(Paragraph("""
    <b>WARNING - ECONOLUBE STANDARD 320 (LUB-003) RESTRICTIONS:</b><br/><br/>

    EconoLube Standard 320 contains ester-based extreme pressure (EP) additives that are
    <b>INCOMPATIBLE</b> with fluorocarbon elastomers (FFKM, FKM, Viton). Contact between
    EconoLube Standard 320 and fluorocarbon seal materials causes:<br/><br/>

    - Elastomer swelling and dimensional changes<br/>
    - Chemical degradation of seal faces<br/>
    - Loss of sealing integrity<br/>
    - Premature mechanical seal failure (typically within 6-10 weeks of exposure)<br/><br/>

    <b>DO NOT USE LUB-003 on any equipment with fluorocarbon/FFKM seals, including:</b><br/>
    - P-101A Primary Feed Pump (John Crane Type 4620 seal with FFKM elastomers)<br/>
    - P-101B Standby Feed Pump (John Crane Type 4620 seal with FFKM elastomers)<br/>
    - Any pump handling hydrocarbons above 80°C<br/><br/>

    Failure to comply with this restriction may result in seal failure, hydrocarbon release,
    and potential safety incidents.
    """, styles['Normal']))
    story.append(Spacer(1, 0.2*inch))

    # Technical basis
    story.append(Paragraph("5. TECHNICAL BASIS", heading_style))
    story.append(Paragraph("""
    <b>Seal Material Compatibility:</b><br/>
    Fluorocarbon elastomers (FFKM/FKM) are susceptible to degradation when exposed to
    ester-based compounds. The ester additives in Group I mineral oils with EP packages
    cause the fluorocarbon polymer chains to absorb the ester molecules, resulting in
    swelling of 15-25% and loss of mechanical properties.<br/><br/>

    <b>OEM Requirements:</b><br/>
    John Crane Technical Bulletin JC-TB-2019-042 specifies that Type 4620 cartridge seals
    with FFKM elastomers require lubricants free of ester-based additives. Use of
    non-compatible lubricants voids the seal warranty.<br/><br/>

    <b>Flowserve Pump Manual Reference:</b><br/>
    Flowserve HPX Series Installation Manual Section 7.3.2 states: "Use only lubricants
    approved for fluorocarbon seal compatibility. Ester-based lubricants will cause
    premature seal failure."
    """, styles['Normal']))
    story.append(Spacer(1, 0.2*inch))

    # Management of Change
    story.append(Paragraph("6. MANAGEMENT OF CHANGE", heading_style))
    story.append(Paragraph("""
    Per OISD-STD-144 Section 4.5.2, any change to approved lubricants requires:<br/><br/>

    1. Technical review by Reliability Engineering<br/>
    2. Compatibility assessment with equipment seal materials<br/>
    3. MOC documentation and approval<br/>
    4. Update to this standard<br/><br/>

    Substitution of lubricants without MOC approval is prohibited.
    """, styles['Normal']))
    story.append(Spacer(1, 0.2*inch))

    # Sign-off
    story.append(Paragraph("DOCUMENT APPROVAL", heading_style))
    story.append(Paragraph("""
    Prepared by: Reliability Engineering<br/>
    Reviewed by: Priya Sharma, Rotating Equipment Specialist<br/>
    Approved by: Rajesh Kumar, Senior Maintenance Engineer<br/>
    Date: 2022-01-15<br/>
    Next Review: 2024-01-15
    """, styles['Normal']))

    doc.build(story)
    print("Created: LUB-STD-001.pdf")


if __name__ == "__main__":
    create_lubrication_standard()
