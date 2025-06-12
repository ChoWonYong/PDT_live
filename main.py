import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import os

# 각 분석기 클래스들을 import
try:
    from nsfw_video import NSFWVideoAnalyzerGUI
    from nsfw_realtime import YouTubeNSFWRealTimeDetector
except ImportError as e:
    print(f"필요한 모듈을 찾을 수 없습니다: {e}")
    print("nsfw_video.py와 nsfw_realtime.py 파일이 같은 폴더에 있는지 확인하세요.")

class UnifiedNSFWAnalyzer:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("NSFW 영상 분석기")
        self.root.geometry("650x600")
        self.root.resizable(True, True)
        
        # 창을 화면 중앙에 배치
        self.center_window()
        
        # 현재 모드 (None, 'realtime', 'local')
        self.current_mode = None
        
        # 로컬 분석기 (재사용을 위해)
        self.local_analyzer = None
        
        self.setup_gui()
        
    def center_window(self):
        """창을 화면 중앙에 배치"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
        
    def setup_gui(self):
        """GUI 설정"""
        # 메인 프레임
        self.main_frame = ttk.Frame(self.root, padding="20")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 제목
        title_label = ttk.Label(self.main_frame, text="NSFW 영상 분석기", 
                               font=("Arial", 20, "bold"))
        title_label.pack(pady=(0, 20))
        
        # 모드 선택 섹션
        self.setup_mode_selection()
        
        # 입력 필드 프레임 (동적으로 변경됨)
        self.input_frame = ttk.Frame(self.main_frame)
        self.input_frame.pack(fill=tk.X, pady=(20, 0))
        
        # 실행 버튼 (처음에는 비활성화)
        self.execute_btn = ttk.Button(self.main_frame, text="분석 시작", 
                                     command=self.execute_analysis, state=tk.DISABLED,
                                     style="Execute.TButton")
        self.execute_btn.pack(pady=(30, 20))
        
        # 진행상황 표시
        self.setup_progress_display()
        
        # 스타일 설정
        self.setup_styles()
        
    def setup_mode_selection(self):
        """모드 선택 섹션 설정"""
        mode_frame = ttk.LabelFrame(self.main_frame, text="분석 모드 선택", padding="15")
        mode_frame.pack(fill=tk.X, pady=(0, 20))
        
        self.mode_var = tk.StringVar()
        
        # 실시간 YouTube 분석 라디오 버튼
        realtime_radio = ttk.Radiobutton(mode_frame, 
                                        text="🎥 실시간 영상 분석", 
                                        variable=self.mode_var, 
                                        value="realtime",
                                        command=self.on_mode_change)
        realtime_radio.pack(anchor=tk.W, pady=(0, 5))
        
        realtime_desc = ttk.Label(mode_frame, 
                                 text="   • URL을 입력받아 실시간으로 NSFW 콘텐츠 탐지\n"
                                      "   • NSFW 탐지 시 즉시 정지",
                                 font=("Arial", 9), foreground="gray")
        realtime_desc.pack(anchor=tk.W, pady=(0, 15))
        
        # 로컬 영상 분석 라디오 버튼
        local_radio = ttk.Radiobutton(mode_frame, 
                                     text="📁 로컬 영상 분석(더 정확)", 
                                     variable=self.mode_var, 
                                     value="local",
                                     command=self.on_mode_change)
        local_radio.pack(anchor=tk.W, pady=(0, 5))
        
        local_desc = ttk.Label(mode_frame, 
                              text="   • 로컬 영상 파일을 업로드하여 전체 분석\n"
                                   "   • NSFW 구간을 제거한 깨끗한 영상 생성",
                              font=("Arial", 9), foreground="gray")
        local_desc.pack(anchor=tk.W)
        
    def setup_progress_display(self):
        """진행상황 표시 섹션 설정"""
        progress_frame = ttk.Frame(self.main_frame)
        progress_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.progress_var = tk.StringVar(value="모드를 선택하고 설정을 입력하세요.")
        progress_label = ttk.Label(progress_frame, textvariable=self.progress_var)
        progress_label.pack()
        
        self.progress_bar = ttk.Progressbar(progress_frame, mode='indeterminate')
        self.progress_bar.pack(fill=tk.X, pady=(10, 0))
        
    def setup_styles(self):
        """스타일 설정"""
        style = ttk.Style()
        style.configure("Execute.TButton", padding=(15, 10), font=("Arial", 12, "bold"))
        
    def on_mode_change(self):
        """모드 변경 시 호출"""
        # 기존 입력 필드 제거
        for widget in self.input_frame.winfo_children():
            widget.destroy()
            
        mode = self.mode_var.get()
        self.current_mode = mode
        
        if mode == "realtime":
            self.setup_realtime_inputs()
        elif mode == "local":
            self.setup_local_inputs()
            
        # 실행 버튼 상태 업데이트
        self.update_execute_button()
        
    def setup_realtime_inputs(self):
        """실시간 분석 입력 필드 설정"""
        # YouTube URL 입력
        url_frame = ttk.LabelFrame(self.input_frame, text="YouTube URL", padding="10")
        url_frame.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Label(url_frame, text="YouTube URL을 입력하세요:", 
                 font=("Arial", 10)).pack(anchor=tk.W)
        
        self.url_var = tk.StringVar()
        self.url_entry = ttk.Entry(url_frame, textvariable=self.url_var, 
                                  font=("Arial", 10))
        self.url_entry.pack(fill=tk.X, pady=(5, 0))
        self.url_entry.bind('<KeyRelease>', self.on_input_change)
        
        # Threshold 입력
        self.setup_threshold_input()
        
    def setup_local_inputs(self):
        """로컬 분석 입력 필드 설정"""
        # 파일 선택
        file_frame = ttk.LabelFrame(self.input_frame, text="영상 파일 선택", padding="10")
        file_frame.pack(fill=tk.X, pady=(0, 15))
        
        self.file_path_var = tk.StringVar(value="선택된 파일 없음")
        file_path_label = ttk.Label(file_frame, textvariable=self.file_path_var, 
                                   foreground="gray")
        file_path_label.pack(fill=tk.X, pady=(0, 10))
        
        select_file_btn = ttk.Button(file_frame, text="영상 파일 선택", 
                                    command=self.select_video_file)
        select_file_btn.pack()
        
        # Threshold 입력
        self.setup_threshold_input()
        
    def setup_threshold_input(self):
        """Threshold 입력 필드 설정"""
        threshold_frame = ttk.LabelFrame(self.input_frame, text="NSFW 탐지 민감도", padding="10")
        threshold_frame.pack(fill=tk.X)
        
        ttk.Label(threshold_frame, text="NSFW 탐지 임계값 (0~100):", 
                 font=("Arial", 12)).pack(anchor=tk.W)
        
        self.threshold_var = tk.StringVar(value="50")
        self.threshold_entry = ttk.Entry(threshold_frame, textvariable=self.threshold_var, 
                                        font=("Arial", 17), width=10)
        self.threshold_entry.pack(anchor=tk.W, pady=(5, 0))
        self.threshold_entry.bind('<KeyRelease>', self.on_input_change)
        
    def select_video_file(self):
        """영상 파일 선택"""
        filepath = filedialog.askopenfilename(
            title="분석할 영상 파일 선택",
            filetypes=[
                ("모든 영상 파일", "*.mp4 *.avi *.mov *.mkv *.wmv *.flv *.webm"),
                ("MP4 파일", "*.mp4"),
                ("AVI 파일", "*.avi"),
                ("MOV 파일", "*.mov"),
                ("MKV 파일", "*.mkv"),
                ("모든 파일", "*.*")
            ]
        )
        
        if filepath:
            self.file_path_var.set(os.path.basename(filepath))
            self.selected_file_path = filepath
        else:
            self.file_path_var.set("선택된 파일 없음")
            self.selected_file_path = None
            
        self.update_execute_button()
        
    def on_input_change(self, event=None):
        """입력값 변경 시 호출"""
        self.update_execute_button()
        
    def update_execute_button(self):
        """실행 버튼 상태 업데이트"""
        can_execute = False
        
        if self.current_mode == "realtime":
            url = getattr(self, 'url_var', tk.StringVar()).get().strip()
            threshold = getattr(self, 'threshold_var', tk.StringVar()).get().strip()
            can_execute = url and threshold and self.validate_inputs_silent()
            
        elif self.current_mode == "local":
            has_file = hasattr(self, 'selected_file_path') and self.selected_file_path
            threshold = getattr(self, 'threshold_var', tk.StringVar()).get().strip()
            can_execute = has_file and threshold and self.validate_inputs_silent()
            
        self.execute_btn.config(state=tk.NORMAL if can_execute else tk.DISABLED)
        
    def validate_inputs_silent(self):
        """입력값 검증 (오류 메시지 없이)"""
        try:
            # Threshold 검증
            threshold = float(self.threshold_var.get())
            if not (0 <= threshold <= 100):
                return False
                
            # URL 검증 (실시간 모드인 경우)
            if self.current_mode == "realtime":
                url = self.url_var.get().strip()
                if not url or ("youtube.com" not in url and "youtu.be" not in url):
                    return False
                    
            return True
        except ValueError:
            return False
            
    def validate_inputs(self):
        """입력값 검증 (오류 메시지 포함)"""
        try:
            # Threshold 검증
            threshold = float(self.threshold_var.get())
            if not (0 <= threshold <= 100):
                messagebox.showerror("입력 오류", "임계값은 0~100 사이의 숫자여야 합니다.")
                return None
                
            threshold = threshold / 100.0  # 0~1 범위로 변환
            
            # 모드별 추가 검증
            if self.current_mode == "realtime":
                url = self.url_var.get().strip()
                if not url:
                    messagebox.showerror("입력 오류", "YouTube URL을 입력해주세요.")
                    return None
                if "youtube.com" not in url and "youtu.be" not in url:
                    messagebox.showerror("입력 오류", "올바른 YouTube URL을 입력해주세요.")
                    return None
                return {"url": url, "threshold": threshold}
                
            elif self.current_mode == "local":
                if not hasattr(self, 'selected_file_path') or not self.selected_file_path:
                    messagebox.showerror("입력 오류", "영상 파일을 선택해주세요.")
                    return None
                return {"file_path": self.selected_file_path, "threshold": threshold}
                
        except ValueError:
            messagebox.showerror("입력 오류", "임계값은 0~100 사이의 숫자여야 합니다.")
            return None
            
    def execute_analysis(self):
        """분석 실행"""
        if not self.current_mode:
            messagebox.showwarning("모드 선택", "분석 모드를 선택해주세요.")
            return
            
        params = self.validate_inputs()
        if not params:
            return
            
        # 버튼 비활성화 및 진행상황 표시
        self.execute_btn.config(state=tk.DISABLED, text="분석 중...")
        self.progress_bar.start()
        
        if self.current_mode == "realtime":
            self.progress_var.set("실시간 분석을 시작합니다...")
            thread = threading.Thread(target=self.run_realtime_analysis, args=(params,))
        else:
            self.progress_var.set("로컬 영상 분석을 시작합니다...")
            thread = threading.Thread(target=self.run_local_analysis, args=(params,))
            
        thread.daemon = True
        thread.start()
        
    def run_realtime_analysis(self, params):
        """실시간 분석 실행"""
        try:
            print(f"\n 설정된 임계값: {params['threshold'] * 100}%")
            print(f" YouTube URL: {params['url']}")
            print("\n 실시간 분석을 시작합니다...")
            
            detector = YouTubeNSFWRealTimeDetector(nsfw_threshold=params['threshold'])
            detector.run_detection(params['url'])
            detector.close()
            
        except Exception as e:
            print(f"실시간 분석 오류: {e}")
            self.root.after(0, lambda: messagebox.showerror("분석 오류", f"실시간 분석 중 오류가 발생했습니다:\n{e}"))
        finally:
            # UI 복원
            self.root.after(0, self.reset_ui)
            
    def run_local_analysis(self, params):
        """로컬 분석 실행"""
        try:
            # NSFWVideoAnalyzerGUI의 analyze_video 메서드를 직접 사용
            if not self.local_analyzer:
                # 임시로 로컬 분석기 생성 (GUI 없이)
                import cv2
                from PIL import Image
                import timm
                import torch
                from datetime import datetime
                import subprocess
                
                class LocalAnalyzer:
                    def __init__(self, main_gui):
                        self.main_gui = main_gui
                        self.video_path = None
                        self.load_model()
                        
                    def load_model(self):
                        """NSFW 모델 로드"""
                        try:
                            self.model = timm.create_model("hf_hub:Marqo/nsfw-image-detection-384", pretrained=True)
                            self.model = self.model.eval()
                            
                            data_config = timm.data.resolve_model_data_config(self.model)
                            self.transforms = timm.data.create_transform(**data_config, is_training=False)
                            
                        except Exception as e:
                            raise Exception(f"NSFW 모델을 로드할 수 없습니다:\n{e}")
                    
                    def predict_nsfw_frame(self, image_path, threshold):
                        """단일 프레임 NSFW 탐지"""
                        try:
                            img = Image.open(image_path).convert('RGB')
                            
                            with torch.no_grad():
                                output = self.model(self.transforms(img).unsqueeze(0)).softmax(dim=-1).cpu()
                            
                            probabilities = output[0]
                            nsfw_prob = float(probabilities[0])
                            sfw_prob = float(probabilities[1])
                            
                            is_nsfw = nsfw_prob >= threshold
                            
                            return {
                                'nsfw_probability': nsfw_prob,
                                'sfw_probability': sfw_prob,
                                'is_nsfw': is_nsfw,
                                'confidence': nsfw_prob * 100
                            }
                        except Exception:
                            return None
                    
                    def merge_overlapping_intervals(self, intervals):
                        """겹치는 구간들을 병합"""
                        if not intervals:
                            return []
                            
                        intervals.sort(key=lambda x: x[0])
                        merged = [intervals[0]]
                        
                        for current in intervals[1:]:
                            last = merged[-1]
                            if current[0] <= last[1]:
                                merged[-1] = (last[0], max(last[1], current[1]))
                            else:
                                merged.append(current)
                                
                        return merged
                    
                    def create_clean_video(self, input_path, remove_intervals, output_path, duration):
                        """NSFW 구간을 제거한 깨끗한 영상 생성"""
                        try:
                            if not remove_intervals:
                                cmd = ['ffmpeg', '-i', input_path, '-c', 'copy', output_path, '-y']
                                subprocess.run(cmd, capture_output=True, check=True)
                                return True, duration
                            
                            merged_intervals = self.merge_overlapping_intervals(remove_intervals)
                            
                            safe_segments = []
                            last_end = 0
                            
                            for start, end in merged_intervals:
                                if last_end < start:
                                    safe_segments.append((last_end, start))
                                last_end = end
                            
                            if last_end < duration:
                                safe_segments.append((last_end, duration))
                            
                            if not safe_segments:
                                return False, 0
                            
                            temp_files = []
                            temp_list_file = "temp_segments_list.txt"
                            
                            for i, (start, end) in enumerate(safe_segments):
                                temp_file = f"temp_segment_{i:03d}.mp4"
                                cmd = [
                                    'ffmpeg', '-i', input_path,
                                    '-ss', str(start),
                                    '-t', str(end - start),
                                    '-c', 'copy',
                                    '-avoid_negative_ts', 'make_zero',
                                    temp_file, '-y'
                                ]
                                subprocess.run(cmd, capture_output=True, check=True)
                                temp_files.append(temp_file)
                            
                            with open(temp_list_file, 'w') as f:
                                for temp_file in temp_files:
                                    f.write(f"file '{temp_file}'\n")
                            
                            cmd = [
                                'ffmpeg', '-f', 'concat', '-safe', '0',
                                '-i', temp_list_file,
                                '-c', 'copy',
                                output_path, '-y'
                            ]
                            subprocess.run(cmd, capture_output=True, check=True)
                            
                            new_duration = sum(end - start for start, end in safe_segments)
                            
                            for temp_file in temp_files:
                                if os.path.exists(temp_file):
                                    os.remove(temp_file)
                            if os.path.exists(temp_list_file):
                                os.remove(temp_list_file)
                            
                            return True, new_duration
                            
                        except Exception as e:
                            print(f"영상 생성 오류: {e}")
                            return False, 0
                    
                    def format_timestamp(self, seconds):
                        """시간 포맷팅"""
                        if seconds >= 60:
                            minutes = int(seconds // 60)
                            remaining_seconds = int(seconds % 60)
                            return f"{minutes}분 {remaining_seconds}초"
                        else:
                            return f"{int(seconds)}초"
                    
                    def analyze_video(self, file_path, threshold):
                        """영상 분석 메인 함수"""
                        self.video_path = file_path
                        
                        self.main_gui.root.after(0, lambda: self.main_gui.progress_var.set("영상 정보 분석 중..."))
                        
                        cap = cv2.VideoCapture(file_path)
                        if not cap.isOpened():
                            raise Exception("영상 파일을 열 수 없습니다.")
                            
                        fps = cap.get(cv2.CAP_PROP_FPS)
                        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                        duration = total_frames / fps
                        
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        output_dir = f"nsfw_analysis_{timestamp}"
                        temp_dir = os.path.join(output_dir, "temp_frames")
                        
                        for dir_path in [output_dir, temp_dir]:
                            os.makedirs(dir_path, exist_ok=True)
                            
                        nsfw_detections = []
                        total_seconds = int(duration) + 1
                        
                        for second in range(total_seconds):
                            self.main_gui.root.after(0, lambda s=second: self.main_gui.progress_var.set(f"분석 중... {s+1}/{total_seconds}초"))
                            
                            target_frame = int(second * fps)
                            cap.set(cv2.CAP_PROP_POS_FRAMES, target_frame)
                            ret, frame = cap.read()
                            
                            if not ret:
                                break
                                
                            temp_path = os.path.join(temp_dir, f"frame_{second:04d}.jpg")
                            cv2.imwrite(temp_path, frame)
                            
                            result = self.predict_nsfw_frame(temp_path, threshold)
                            
                            if result and result['is_nsfw']:
                                nsfw_detections.append({
                                    'timestamp': second,
                                    'confidence': result['confidence'],
                                    'formatted_time': self.format_timestamp(second)
                                })
                                
                            if os.path.exists(temp_path):
                                os.remove(temp_path)
                                
                        cap.release()
                        
                        self.main_gui.root.after(0, lambda: self.main_gui.progress_var.set("NSFW 구간 제거된 영상 생성 중..."))
                        
                        remove_intervals = []
                        for detection in nsfw_detections:
                            timestamp = detection['timestamp']
                            start_time = max(0, timestamp - 1)
                            end_time = min(duration, timestamp + 1)
                            remove_intervals.append((start_time, end_time))
                        
                        clean_filename = f"clean_video_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
                        clean_path = os.path.join(output_dir, clean_filename)
                        
                        success, new_duration = self.create_clean_video(
                            file_path, remove_intervals, clean_path, duration
                        )
                        
                        try:
                            if os.path.exists(temp_dir) and not os.listdir(temp_dir):
                                os.rmdir(temp_dir)
                        except:
                            pass
                        
                        # 결과 알림
                        nsfw_count = len(nsfw_detections)
                        
                        if nsfw_count > 0:
                            if success:
                                message = (f"영상 분석이 완료되었습니다!\n\n"
                                         f"🔞 NSFW 콘텐츠 {nsfw_count}개 탐지\n"
                                         f"✅ 정화된 영상이 생성되었습니다\n"
                                         f"파일명: {clean_filename}\n\n"
                                         f"저장 위치: {output_dir}")
                                self.main_gui.root.after(0, lambda: messagebox.showinfo("분석 완료", message))
                            else:
                                message = (f"영상 분석이 완료되었습니다.\n\n"
                                         f"🔞 NSFW 콘텐츠 {nsfw_count}개 탐지\n"
                                         f"영상 정화에 실패했습니다")
                                self.main_gui.root.after(0, lambda: messagebox.showwarning("분석 완료", message))
                        else:
                            message = (f"영상 분석이 완료되었습니다!\n\n"
                                     f"✅ NSFW 콘텐츠가 탐지되지 않았습니다\n"
                                     f"영상이 안전합니다.")
                            self.main_gui.root.after(0, lambda: messagebox.showinfo("분석 완료", message))
                
                self.local_analyzer = LocalAnalyzer(self)
            
            self.local_analyzer.analyze_video(params['file_path'], params['threshold'])
            
        except Exception as e:
            print(f"로컬 분석 오류: {e}")
            self.root.after(0, lambda: messagebox.showerror("분석 오류", f"로컬 분석 중 오류가 발생했습니다:\n{e}"))
        finally:
            # UI 복원
            self.root.after(0, self.reset_ui)
            
    def reset_ui(self):
        """UI 상태 복원"""
        self.execute_btn.config(state=tk.NORMAL, text="분석 시작")
        self.progress_bar.stop()
        self.progress_var.set("분석이 완료되었습니다.")
        self.update_execute_button()
        
    def run(self):
        """GUI 실행"""
        self.root.mainloop()

def main():
    """메인 실행 함수"""
    print("NSFW 영상 분석 시작")
    
    try:
        app = UnifiedNSFWAnalyzer()
        app.run()
    except Exception as e:
        print(f"실행 오류: {e}")

if __name__ == "__main__":
    main() 