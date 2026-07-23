import os
import time
import random
import json
from dotenv import load_dotenv
from groq import Groq
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

if "GROQ_API_KEY" not in os.environ:
    print("❌ ERROR: GROQ_API_KEY not found in environment. Please add it to your .env file.")
    exit(1)

client = Groq()
SEVERITIES = ["Critical", "Major", "Minor", "Warning"]

def load_topology_nodes():
    topology_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data', 'network_topology.json'))
    with open(topology_path, 'r') as f:
        data = json.load(f)
    return data.get("network_topology", {}).get("nodes", [])

def generate_sop_json(node_id, vendor, role, alarm_code, severity):
    prompt = f"""
    You are an elite Telecom Network Engineer. Create a highly technical Standard Operating Procedure (SOP).
    
    Node ID: {node_id}
    Vendor: {vendor}
    Role: {role}
    Alarm Code: ALARM_{alarm_code}
    Severity: {severity}
    
    Return the output STRICTLY as a JSON object with the following keys:
    - "title": A professional title for the SOP.
    - "description": A brief technical description of the alarm.
    - "root_causes": A list of dictionaries, each with "Cause" and "Probability" (High/Medium/Low).
    - "diagnostic_commands": A list of CLI commands to diagnose the issue.
    - "resolution_steps": A list of step-by-step resolution actions (include CLI commands if applicable).
    - "verification_commands": A list of CLI commands to verify the fix.
    
    Ensure the JSON is valid and properly escaped.
    """
    
    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.7,
            max_tokens=1500,
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        print(f"Error generating SOP JSON for ALARM_{alarm_code} on {node_id}: {e}")
        return None

def save_as_styled_pdf(data, pdf_filepath, node_id, vendor, alarm_code, severity):
    doc = SimpleDocTemplate(pdf_filepath, pagesize=letter)
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'EnterpriseTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=18,
        textColor=colors.HexColor('#1F4E79'),
        spaceAfter=14
    )
    
    header_style = ParagraphStyle(
        'EnterpriseHeader',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=14,
        textColor=colors.HexColor('#2E75B6'),
        spaceBefore=12,
        spaceAfter=8
    )
    
    normal_style = ParagraphStyle(
        'EnterpriseNormal',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        textColor=colors.HexColor('#333333'),
        spaceAfter=6
    )
    
    cli_style = ParagraphStyle(
        'EnterpriseCLI',
        parent=styles['Code'],
        fontName='Courier',
        fontSize=10,
        textColor=colors.HexColor('#E2EFDA'),
        backColor=colors.HexColor('#333333'),
        borderPadding=6,
        spaceAfter=8
    )

    Story = []
    
    # Implicit strings needed by Chunking Regex (now including Node ID)
    hidden_meta = f"<font color='white' size='1'>ALARM_CODE_{alarm_code} Severity: {severity} NodeID: {node_id}</font>"
    Story.append(Paragraph(hidden_meta, normal_style))
    
    Story.append(Paragraph(data.get('title', f"SOP for {node_id}"), title_style))
    
    meta_text = f"<b>Node:</b> {node_id} | <b>Vendor:</b> {vendor} | <b>Severity:</b> {severity} | <b>Alarm Code:</b> ALARM_{alarm_code}"
    Story.append(Paragraph(meta_text, normal_style))
    Story.append(Spacer(1, 12))
    
    Story.append(Paragraph("Description", header_style))
    Story.append(Paragraph(data.get('description', ''), normal_style))
    
    Story.append(Paragraph("Potential Root Causes", header_style))
    causes = data.get('root_causes', [])
    if causes:
        table_data = [["Cause", "Probability"]]
        for c in causes:
            table_data.append([c.get("Cause", ""), c.get("Probability", "")])
            
        t = Table(table_data, colWidths=[350, 100])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (1,0), colors.HexColor('#1F4E79')),
            ('TEXTCOLOR', (0,0), (1,0), colors.whitesmoke),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0,0), (-1,0), 12),
            ('BACKGROUND', (0,1), (-1,-1), colors.HexColor('#F2F2F2')),
            ('GRID', (0,0), (-1,-1), 1, colors.HexColor('#D9D9D9')),
        ]))
        Story.append(t)
        Story.append(Spacer(1, 12))
        
    Story.append(Paragraph("Diagnostic Commands", header_style))
    for cmd in data.get('diagnostic_commands', []):
        Story.append(Paragraph(cmd, cli_style))
        
    Story.append(Paragraph("Resolution Steps", header_style))
    for i, step in enumerate(data.get('resolution_steps', [])):
        Story.append(Paragraph(f"Step {i+1}: {step}", normal_style))
        
    Story.append(Paragraph("Post-Check Verification", header_style))
    for cmd in data.get('verification_commands', []):
        Story.append(Paragraph(cmd, cli_style))

    doc.build(Story)

def main():
    output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data', 'llm_generated_sops'))
    os.makedirs(output_dir, exist_ok=True)
    
    nodes = load_topology_nodes()
    if not nodes:
        print("❌ ERROR: No nodes found in topology.")
        return
        
    print(f"🚀 Starting Node-Aware SOP Generation ({len(nodes)} nodes available)...")
    
    TOTAL_TO_GENERATE = 1000 
    generated_set = set()
    generated = 0
    
    while generated < TOTAL_TO_GENERATE:
        node = random.choice(nodes)
        node_id = node["node_id"]
        vendor = node["vendor"]
        role = node["role"]
        
        alarm_code = random.randint(1000, 9999)
        severity = random.choice(SEVERITIES)
        
        # Enforce exact uniqueness
        combo_key = f"{node_id}_{alarm_code}"
        if combo_key in generated_set:
            continue
            
        filename = f"{node_id.upper()}_ALARM_{alarm_code}_SOP.pdf"
        filepath = os.path.join(output_dir, filename)
        
        if os.path.exists(filepath):
            continue
            
        print(f"Generating {generated+1}/{TOTAL_TO_GENERATE}: {node_id} (ALARM_{alarm_code})...")
        
        sop_data = generate_sop_json(node_id, vendor, role, alarm_code, severity)
        
        if sop_data:
            try:
                save_as_styled_pdf(sop_data, filepath, node_id, vendor, alarm_code, severity)
                print(f"✅ Saved: {filename}")
                generated_set.add(combo_key)
                generated += 1
            except Exception as e:
                print(f"Failed to save PDF {filename}: {e}")
            
        time.sleep(2)
        
    print(f"\\n🎉 Successfully generated {TOTAL_TO_GENERATE} node-linked SOPs.")

if __name__ == "__main__":
    main()
