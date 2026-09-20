import os
import json
import random
from dotenv import load_dotenv
from groq import Groq

# Load variables
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

if "GROQ_API_KEY" not in os.environ:
    print("Error: GROQ_API_KEY was not found. Add it to the .env file.")
    exit(1)

client = Groq()

def generate_syslog(node_id, alarm_code):
    prompt = f"Generate a single line realistic raw network syslog message indicating that node {node_id} is experiencing an alarm condition corresponding to alarm code {alarm_code}. The syslog must include the node ID and the alarm code. Do not output anything else. Example format: 'Mar 12 10:00:00 {node_id} %SYS-5-CONFIG_I: ALARM_{alarm_code} configured from console by vty0'"
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=200,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error generating syslog for ALARM_{alarm_code} on {node_id}: {e}")
        return f"Mar 12 10:00:00 {node_id} ALARM: Node experiencing critical failure with alarm code {alarm_code}"

def main():
    sops_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data', 'sops'))
    if not os.path.exists(sops_dir):
        print(f"Error: {sops_dir} does not exist. Run generate_sops_pdf.py first to generate the SOPs.")
        return
        
    all_sops = [f for f in os.listdir(sops_dir) if f.endswith('.pdf')]
    if not all_sops:
        print("No SOPs found in directory.")
        return
        
    # Pick up to 50 random SOPs to create the Golden Dataset
    sample_size = min(50, len(all_sops))
    sampled_sops = random.sample(all_sops, sample_size)
    
    dataset = []
    print(f"Generating golden dataset for {sample_size} SOPs...")
    
    for i, sop in enumerate(sampled_sops):
        print(f"Processing {i+1}/{sample_size}: {sop}")
        # Assumes filename format: BLR-CORE-01_ALARM_1234_SOP.pdf
        parts = sop.replace('_SOP.pdf', '').split('_ALARM_')
        if len(parts) == 2:
            node_id = parts[0]
            alarm_code = parts[1]
            syslog = generate_syslog(node_id, alarm_code)
            dataset.append({
                "question": syslog,
                "expected_document_name": sop
            })
            
    output_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'eval_dataset.json')
    with open(output_path, 'w') as f:
        json.dump(dataset, f, indent=4)
        
    print(f"Successfully generated Golden Dataset with {len(dataset)} entries at {output_path}")

if __name__ == "__main__":
    main()
