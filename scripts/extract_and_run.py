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
    file1 = "/Users/tanue/Library/CloudStorage/OneDrive-个人/1科研工作/投稿/基于路面附着系数评估的未知情况下车辆状态评估/5.15学术会议/ОЦЕНКА КОЭФФИЦИЕНТА СЦЕПЛЕНИЯ ДОРОЖНОГО ПОКРЫТИЯ НА ОСНОВЕ АДАПТИВНОГО РАСШИРЕННОГО НАБЛЮДАТЕЛЯ С ИСПОЛЬЗОВАНИЕМ РЕКУРЕНТНОЙ НЕЙРОННОЙ СЕТИ.docx"
    file2 = "/Users/tanue/Desktop/Координированное модельно.docx"
    
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
