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

# Load variables from the local environment file.
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

if "GROQ_API_KEY" not in os.environ:
    print("Error: GROQ_API_KEY was not found. Add it to the .env file.")
    exit(1)

client = Groq()
SEVERITIES = ["Critical", "Major", "Minor", "Warning"]

FAILURE_DOMAINS = [
    "Optical Transport Failure (SFP/XFP degradation, fiber cuts, Rx/Tx power loss)",
    "Routing Protocol Flap (BGP route churn, OSPF adjacency loss, ISIS LSP flooding)",
    "Hardware/Environmental Fault (ASIC memory parity errors, line card crashes, power supply redundancy loss)",
    "QoS / Congestion Event (Microbursts, interface tail drops, QoS queue starvation)"
]

LOCATIONS = {
    "KOR": "Koramangala Datacenter",
    "WFD": "Whitefield POP",
    "IND": "Indiranagar Exchange",
    "MG": "MG Road Core",
    "BTM": "BTM Layout Aggregation",
    "ELEC": "Electronic City Hub",
    "HSR": "HSR Layout Access",
    "MALL": "Malleswaram Node",
    "JAY": "Jayanagar Metro Site",
    "BAS": "Basavanagudi POP",
    "YEL": "Yelahanka Sub-station",
    "HEB": "Hebbal Edge",
    "MAR": "Marathahalli Core",
    "WHI": "Whitefield East POP",
    "KR": "KR Puram Access"
}

def load_topology_nodes():
    topology_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data', 'network_topology.json'))
    with open(topology_path, 'r') as f:
        data = json.load(f)
    return data.get("network_topology", {}).get("nodes", [])

def generate_sop_json(node_id, vendor, role, alarm_code, severity):
    loc_prefix = node_id.split("-")[0]
    site_location = LOCATIONS.get(loc_prefix, "Unknown Site")
    failure_domain = random.choice(FAILURE_DOMAINS)
    
    prompt = f"""
    You are an elite Telecom Network Architect (Senior MTS). Create a highly technical and verbose Standard Operating Procedure (SOP).
    
    Failure Context:
    Node ID: {node_id}
    Site Location: {site_location}
    Vendor (CLI Dialect): {vendor}
    Role: {role}
    Failure Domain: {failure_domain}
    Alarm Code: ALARM_{alarm_code}
    Severity: {severity}
    
    You MUST adhere strictly to the CLI dialect of the Vendor specified ({vendor}) for all diagnostic and resolution commands.
    
    Return the output STRICTLY as a JSON object with the following keys:
    - "title": A professional, vendor-specific title for the SOP.
    - "description": A highly verbose (150+ words) architectural description of *why* this failure domain occurs on this specific role and vendor equipment, explaining the underlying protocol or hardware mechanics.
    - "prerequisites": A list of pre-requisite physical or environmental checks before proceeding (e.g., dispatching remote hands to {site_location}, checking redundant link status).
    - "root_causes": A list of dictionaries, each with "Cause" and "Probability" (High/Medium/Low).
    - "diagnostic_commands": A list of dictionaries, each with "Command" (exact vendor CLI), "Expected Output", and "Description" (Deep explanation of what the command isolates in the control or data plane).
    - "resolution_steps": A list of dictionaries, each with "Step" (title), "Command" (vendor CLI), and "Description" (detailed explanation of the fix).
    - "verification_commands": A list of dictionaries with "Command", "Expected Output", and "Description".
    - "rollback_procedures": A list of dictionaries with "Step", "Command", and "Description" to safely rollback if the fix fails.
    
    Ensure the JSON is valid and properly escaped.
    """
    
    try:
        response = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are a senior network engineer generating raw troubleshooting data in strict JSON format."},
                {"role": "user", "content": prompt}
            ],
            model="llama-3.3-70b-versatile",
            response_format={"type": "json_object"},
            temperature=0.7,
            max_tokens=4000,
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        error_msg = str(e)
        if "429" in error_msg or "rate limit" in error_msg.lower():
            if "per day" in error_msg.lower() or "tpd" in error_msg.lower():
                print(f"Daily token limit reached! Exiting script gracefully. Try again tomorrow.")
                exit(0)
            print(f"Rate limit hit while generating SOP for ALARM_{alarm_code} on {node_id}. Sleeping for 65 seconds...")
            time.sleep(65)
            # We return "RATE_LIMIT" to let the loop know it should retry the exact same node instead of skipping
            return "RATE_LIMIT"
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
    
    # Keep metadata in the PDF text so the ingestion regex can find it.
    hidden_meta = f"<font color='white' size='1'>ALARM_CODE_{alarm_code} Severity: {severity} NodeID: {node_id}</font>"
    Story.append(Paragraph(hidden_meta, normal_style))
    
    Story.append(Paragraph(data.get('title', f"SOP for {node_id}"), title_style))
    
    meta_text = f"<b>Node:</b> {node_id} | <b>Vendor:</b> {vendor} | <b>Severity:</b> {severity} | <b>Alarm Code:</b> ALARM_{alarm_code}"
    Story.append(Paragraph(meta_text, normal_style))
    Story.append(Spacer(1, 12))
    
    Story.append(Paragraph("Description", header_style))
    Story.append(Paragraph(data.get('description', ''), normal_style))
    
    Story.append(Paragraph("Pre-requisite Checks", header_style))
    for req in data.get('prerequisites', []):
        if isinstance(req, dict):
            req = ", ".join(f"{k}: {v}" for k, v in req.items())
        Story.append(Paragraph(f"- {req}", normal_style))
        
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
        
    Story.append(Paragraph("Diagnostic Commands & Expected Outputs", header_style))
    for cmd in data.get('diagnostic_commands', []):
        if isinstance(cmd, dict):
            cmd = ", ".join(f"{k}: {v}" for k, v in cmd.items())
        Story.append(Paragraph(str(cmd), cli_style))
        
    Story.append(Paragraph("Resolution Steps", header_style))
    for i, step in enumerate(data.get('resolution_steps', [])):
        if isinstance(step, dict):
            step = ", ".join(f"{k}: {v}" for k, v in step.items())
        Story.append(Paragraph(f"Step {i+1}: {step}", normal_style))
        
    Story.append(Paragraph("Post-Check Verification", header_style))
    for cmd in data.get('verification_commands', []):
        if isinstance(cmd, dict):
            cmd = ", ".join(f"{k}: {v}" for k, v in cmd.items())
        Story.append(Paragraph(str(cmd), cli_style))
        
    Story.append(Paragraph("Roll-back Procedures", header_style))
    for rb in data.get('rollback_procedures', []):
        if isinstance(rb, dict):
            rb = ", ".join(f"{k}: {v}" for k, v in rb.items())
        Story.append(Paragraph(f"- {rb}", normal_style))

    doc.build(Story)

def main():
    output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data', 'sops'))
    os.makedirs(output_dir, exist_ok=True)
    
    nodes = load_topology_nodes()
    if not nodes:
        print("Error: No nodes were found in the topology file.")
        return
        
    print(f"Starting High-Fidelity SOP generation with {len(nodes)} available nodes.")
    
    TOTAL_TO_GENERATE = 700 
    generated_set = set()
    
    # Pre-scan existing files to avoid duplicates and accurately resume count
    existing_files = [f for f in os.listdir(output_dir) if f.endswith(".pdf")]
    for f in existing_files:
        # Expected format: NODE-ID_ALARM_1234_SOP.pdf
        parts = f.replace("_SOP.pdf", "").split("_ALARM_")
        if len(parts) == 2:
            combo_key = f"{parts[0]}_{parts[1]}"
            generated_set.add(combo_key)
            
    generated = len(generated_set)
    print(f"Found {generated} existing SOPs. Generating {TOTAL_TO_GENERATE - generated} more to reach {TOTAL_TO_GENERATE}.")
    
    while generated < TOTAL_TO_GENERATE:
        node = random.choice(nodes)
        node_id = node["node_id"]
        vendor = node["vendor"]
        role = node["role"]
        
        alarm_code = random.randint(1000, 9999)
        severity = random.choice(SEVERITIES)
        
        # Do not generate the same node and alarm-code pair twice.
        combo_key = f"{node_id}_{alarm_code}"
        if combo_key in generated_set:
            continue
            
        filename = f"{node_id.upper()}_ALARM_{alarm_code}_SOP.pdf"
        filepath = os.path.join(output_dir, filename)
        
        if os.path.exists(filepath):
            continue
            
        print(f"Generating {generated + 1} of {TOTAL_TO_GENERATE}: {node_id}, ALARM_{alarm_code}.")
        
        sop_data = generate_sop_json(node_id, vendor, role, alarm_code, severity)
        
        if sop_data == "RATE_LIMIT":
            # Do not increment generated count, and do not add to generated_set
            # The node will simply be skipped and another random node will be chosen next iteration
            continue
            
        if sop_data:
            try:
                save_as_styled_pdf(sop_data, filepath, node_id, vendor, alarm_code, severity)
                print(f"Saved: {filename}")
                generated_set.add(combo_key)
                generated += 1
            except Exception as e:
                print(f"Failed to save PDF {filename}: {e}")
            
        # Sleep for 4 seconds between requests to avoid hitting the RPM limits
        time.sleep(4)
        
    print(f"Generated {TOTAL_TO_GENERATE} node-linked SOPs.")

if __name__ == "__main__":
    main()
