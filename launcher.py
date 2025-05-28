import os
import tkinter as tk
from tkinter import filedialog, messagebox
import subprocess
import cv2
from utils import detect_nsfw_from_image


def run_url_mode():
    subprocess.run(["python", "main.py"])  # main.py는 YouTube URL 분석


def run_file_mode():
    filepath = filedialog.askopenfilename(filetypes=[("Video files", "*.mp4 *.avi *.mov *.mkv")])
    if not filepath:
        messagebox.showinfo("취소됨", "파일이 선택되지 않았습니다.")
        return

    report_lines = []
    explicit_times = []

    cap = cv2.VideoCapture(filepath)
    fps = cap.get(cv2.CAP_PROP_FPS)
    interval = int(fps * 1)  # 1초에 한 프레임 검사

    frame_idx = 0
    frame_number = 0
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    temp_dir = "temp_frames"
    os.makedirs(temp_dir, exist_ok=True)

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        if frame_idx % interval == 0:
            temp_path = os.path.join(temp_dir, f"frame_{frame_number}.jpg")
            cv2.imwrite(temp_path, frame)
            result = detect_nsfw_from_image(temp_path)

            if result["is_nsfw"] and result["confidence_percentage"] > 70.0:
                timestamp = round(frame_idx / fps, 1)
                explicit_times.append(timestamp)
                report_lines.append(f"{timestamp}초: NSFW (신뢰도 {result['confidence_percentage']}%)")

            os.remove(temp_path)
            frame_number += 1

        frame_idx += 1

    cap.release()

    report = "🔍 영상 외설 분석 보고서\n"
    report += f"파일명: {os.path.basename(filepath)}\n"
    report += f"총 프레임 수: {total_frames}, 분석 프레임 수: {frame_number}\n\n"
    if explicit_times:
        report += "⚠️ 외설 콘텐츠 발견됨!\n"
        report += "\n".join(report_lines)
    else:
        report += "✅ 외설 콘텐츠가 감지되지 않았습니다."

    with open("nsfw_report.txt", "w", encoding="utf-8") as f:
        f.write(report)

    messagebox.showinfo("분석 완료", "보고서가 'nsfw_report.txt'로 저장되었습니다.")


def launch_gui():
    root = tk.Tk()
    root.title("NSFW 영상 분석기")
    root.geometry("400x250")
    root.configure(bg="white")

    tk.Label(root, text="모드를 선택하세요", font=("Arial", 16), bg="white").pack(pady=20)

    tk.Button(root, text="1. URL 입력 모드 (YouTube)", font=("Arial", 14), width=30, command=run_url_mode).pack(pady=10)
    tk.Button(root, text="2. 영상 파일 분석 모드", font=("Arial", 14), width=30, command=run_file_mode).pack(pady=10)
    tk.Button(root, text="3. (미정)", font=("Arial", 14), width=30, state=tk.DISABLED).pack(pady=10)

    root.mainloop()


if __name__ == "__main__":
    launch_gui()
