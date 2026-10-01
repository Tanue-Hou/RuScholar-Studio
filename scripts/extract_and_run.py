import os
import sys
import docx2txt
import subprocess

def extract_text(docx_path, out_path):
    print(f"Extracting: {docx_path}")
    try:
        text = docx2txt.process(docx_path)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"Saved to {out_path}")
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False

def main():
    file1 = sys.argv[1] if len(sys.argv) > 1 else os.getenv("TEST_DOCX_FILE_1", "examples/manuscript_sample_1.docx")
    file2 = sys.argv[2] if len(sys.argv) > 2 else os.getenv("TEST_DOCX_FILE_2", "examples/manuscript_sample_2.docx")
    
    out1 = "scratch/test1_ai_assisted.txt"
    out2 = "scratch/test2_pure_ai.txt"
    
    os.makedirs("scratch", exist_ok=True)
    
    if extract_text(file1, out1):
        print("\n--- Running Diagnostics on AI Assisted (Modified) ---")
        subprocess.run(["python", "scripts/style_diagnostics.py", "--file", out1])
        
    if extract_text(file2, out2):
        print("\n--- Running Diagnostics on Pure AI ---")
        subprocess.run(["python", "scripts/style_diagnostics.py", "--file", out2])

if __name__ == "__main__":
    main()
