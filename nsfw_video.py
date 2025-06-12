# 로컬 영상 분석기

import os
import cv2
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image
import timm
import torch
from datetime import datetime
import threading
import subprocess

class NSFWVideoAnalyzerGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("NSFW 영상 분석기")
        self.root.geometry("500x400")
        self.root.resizable(False, False)
        
        # 모델 로드 (한 번만)
        self.model = None
        self.transforms = None
        self.load_model()
        
        self.setup_gui()
        
    def load_model(self):
        """NSFW 모델 로드"""
        try:
            self.model = timm.create_model("hf_hub:Marqo/nsfw-image-detection-384", pretrained=True)
            self.model = self.model.eval()
            
            data_config = timm.data.resolve_model_data_config(self.model)
            self.transforms = timm.data.create_transform(**data_config, is_training=False)
            
        except Exception as e:
            messagebox.showerror("모델 로드 오류", f"NSFW 모델을 로드할 수 없습니다:\n{e}")
            
    def setup_gui(self):
        """GUI 설정"""
        # 메인 프레임
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 제목
        title_label = ttk.Label(main_frame, text="NSFW 영상 분석기", 
                               font=("Arial", 16, "bold"))
        title_label.pack(pady=(0, 20))
        
        # Threshold 입력 섹션
        threshold_frame = ttk.LabelFrame(main_frame, text="설정", padding="10")
        threshold_frame.pack(fill=tk.X, pady=(0, 20))
        
        ttk.Label(threshold_frame, text="기준치를 입력하시오. (0~100):", 
                 font=("Arial", 10)).pack(anchor=tk.W)
        
        self.threshold_var = tk.StringVar(value="50")
        threshold_entry = ttk.Entry(threshold_frame, textvariable=self.threshold_var, 
                                   font=("Arial", 12), width=10)
        threshold_entry.pack(anchor=tk.W, pady=(5, 0))
        
        # 영상 선택 섹션
        video_frame = ttk.LabelFrame(main_frame, text="영상 선택", padding="10")
        video_frame.pack(fill=tk.X, pady=(0, 20))
        
        self.video_path_var = tk.StringVar(value="선택된 파일 없음")
        video_path_label = ttk.Label(video_frame, textvariable=self.video_path_var, 
                                    foreground="gray")
        video_path_label.pack(fill=tk.X, pady=(0, 10))
        
        select_video_btn = ttk.Button(video_frame, text="영상 파일 선택", 
                                     command=self.select_video)
        select_video_btn.pack()
        
        # 분석 버튼
        self.analyze_btn = ttk.Button(main_frame, text="🔍 분석 시작", 
                                     command=self.start_analysis, state=tk.DISABLED)
        self.analyze_btn.pack(pady=20)
        
        # 진행상황 표시
        progress_frame = ttk.Frame(main_frame)
        progress_frame.pack(fill=tk.X, pady=(0, 20))
        
        self.progress_var = tk.StringVar(value="대기 중...")
        progress_label = ttk.Label(progress_frame, textvariable=self.progress_var)
        progress_label.pack()
        
        self.progress_bar = ttk.Progressbar(progress_frame, mode='indeterminate')
        self.progress_bar.pack(fill=tk.X, pady=(10, 0))
        
        # 결과 표시
        result_frame = ttk.LabelFrame(main_frame, text="결과", padding="10")
        result_frame.pack(fill=tk.BOTH, expand=True)
        
        self.result_text = tk.Text(result_frame, height=8, wrap=tk.WORD, 
                                  font=("Arial", 9))
        scrollbar = ttk.Scrollbar(result_frame, orient=tk.VERTICAL, 
                                 command=self.result_text.yview)
        self.result_text.configure(yscrollcommand=scrollbar.set)
        
        self.result_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
    def select_video(self):
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
            self.video_path_var.set(os.path.basename(filepath))
            self.video_path = filepath
            self.analyze_btn.config(state=tk.NORMAL)
        else:
            self.video_path_var.set("선택된 파일 없음")
            self.analyze_btn.config(state=tk.DISABLED)
            
    def validate_threshold(self):
        """Threshold 값 검증"""
        try:
            threshold = float(self.threshold_var.get())
            if 0 <= threshold <= 100:
                return threshold / 100.0  # 0~1 범위로 변환
            else:
                raise ValueError()
        except ValueError:
            messagebox.showerror("입력 오류", "Threshold는 0~100 사이의 숫자여야 합니다.")
            return None
            
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
            
        # 시작 시간으로 정렬
        intervals.sort(key=lambda x: x[0])
        merged = [intervals[0]]
        
        for current in intervals[1:]:
            last = merged[-1]
            # 겹치거나 인접한 구간이면 병합
            if current[0] <= last[1]:
                merged[-1] = (last[0], max(last[1], current[1]))
            else:
                merged.append(current)
                
        return merged
    
    def create_clean_video(self, input_path, remove_intervals, output_path, duration):
        """NSFW 구간을 제거한 깨끗한 영상 생성"""
        try:
            if not remove_intervals:
                # 제거할 구간이 없으면 원본 복사
                cmd = ['ffmpeg', '-i', input_path, '-c', 'copy', output_path, '-y']
                subprocess.run(cmd, capture_output=True, check=True)
                return True, duration
            
            # 겹치는 구간 병합
            merged_intervals = self.merge_overlapping_intervals(remove_intervals)
            
            # 안전한 구간들 계산
            safe_segments = []
            last_end = 0
            
            for start, end in merged_intervals:
                if last_end < start:
                    safe_segments.append((last_end, start))
                last_end = end
            
            # 마지막 구간 추가
            if last_end < duration:
                safe_segments.append((last_end, duration))
            
            if not safe_segments:
                return False, 0  # 모든 구간이 제거됨
            
            # 임시 파일들 생성
            temp_files = []
            temp_list_file = "temp_segments_list.txt"
            
            # 각 안전한 구간을 별도 파일로 추출
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
            
            # concat 리스트 파일 생성
            with open(temp_list_file, 'w') as f:
                for temp_file in temp_files:
                    f.write(f"file '{temp_file}'\n")
            
            # 모든 구간을 하나로 합치기
            cmd = [
                'ffmpeg', '-f', 'concat', '-safe', '0',
                '-i', temp_list_file,
                '-c', 'copy',
                output_path, '-y'
            ]
            subprocess.run(cmd, capture_output=True, check=True)
            
            # 새로운 영상 길이 계산
            new_duration = sum(end - start for start, end in safe_segments)
            
            # 임시 파일들 정리
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
            
    def analyze_video(self, threshold):
        """영상 분석 메인 함수"""
        try:
            # GUI 업데이트
            self.progress_var.set("영상 정보 분석 중...")
            self.progress_bar.start()
            self.root.update()
            
            # 영상 열기
            cap = cv2.VideoCapture(self.video_path)
            if not cap.isOpened():
                raise Exception("영상 파일을 열 수 없습니다.")
                
            fps = cap.get(cv2.CAP_PROP_FPS)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            duration = total_frames / fps
            
            # 결과 저장 디렉토리
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_dir = f"nsfw_analysis_{timestamp}"
            temp_dir = os.path.join(output_dir, "temp_frames")
            
            for dir_path in [output_dir, temp_dir]:
                os.makedirs(dir_path, exist_ok=True)
                
            nsfw_detections = []
            total_seconds = int(duration) + 1
            
            # 프레임별 분석
            for second in range(total_seconds):
                self.progress_var.set(f"분석 중... {second+1}/{total_seconds}초")
                self.root.update()
                
                target_frame = int(second * fps)
                cap.set(cv2.CAP_PROP_POS_FRAMES, target_frame)
                ret, frame = cap.read()
                
                if not ret:
                    break
                    
                # 임시 저장
                temp_path = os.path.join(temp_dir, f"frame_{second:04d}.jpg")
                cv2.imwrite(temp_path, frame)
                
                # NSFW 분석
                result = self.predict_nsfw_frame(temp_path, threshold)
                
                if result and result['is_nsfw']:
                    nsfw_detections.append({
                        'timestamp': second,
                        'confidence': result['confidence'],
                        'formatted_time': self.format_timestamp(second)
                    })
                    
                # 임시 파일 삭제
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                    
            cap.release()
            
            # NSFW 구간을 제거한 깨끗한 영상 생성
            self.progress_var.set("NSFW 구간 제거된 영상 생성 중...")
            self.root.update()
            
            # 제거할 구간들 계산 (각 NSFW 탐지 지점 앞뒤 1초씩)
            remove_intervals = []
            for detection in nsfw_detections:
                timestamp = detection['timestamp']
                start_time = max(0, timestamp - 1)  # 앞 1초
                end_time = min(duration, timestamp + 1)  # 뒤 1초
                remove_intervals.append((start_time, end_time))
            
            # 깨끗한 영상 생성
            clean_filename = f"clean_video_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
            clean_path = os.path.join(output_dir, clean_filename)
            
            success, new_duration = self.create_clean_video(
                self.video_path, remove_intervals, clean_path, duration
            )
            
            # 결과 정리
            result_info = {
                'original_duration': duration,
                'clean_duration': new_duration,
                'removed_duration': duration - new_duration,
                'clean_filename': clean_filename if success else None,
                'nsfw_detections': nsfw_detections,
                'remove_intervals': remove_intervals
            }
                    
            # 임시 디렉토리 정리
            try:
                if os.path.exists(temp_dir) and not os.listdir(temp_dir):
                    os.rmdir(temp_dir)
            except:
                pass
                
            # 보고서 생성
            self.generate_report(output_dir, result_info, threshold, total_seconds)
            
            # 결과 표시
            self.show_results(result_info, output_dir)
            
            # 분석 완료 알림
            nsfw_count = len(result_info['nsfw_detections'])
            clean_filename = result_info['clean_filename']
            
            if nsfw_count > 0:
                if clean_filename:
                    messagebox.showinfo("분석 완료", 
                        f"영상 분석이 완료되었습니다\n\n"
                        f"🔞 NSFW 콘텐츠 {nsfw_count}개 탐지\n"
                        f"✅ 정화된 영상이 생성되었습니다\n"
                        f"파일명: {clean_filename}\n\n"
                        f"저장 위치: {output_dir}")
                else:
                    messagebox.showwarning("분석 완료", 
                        f"영상 분석이 완료되었습니다\n\n"
                        f"🔞 NSFW 콘텐츠 {nsfw_count}개 탐지\n"
                        f"영상 정화에 실패했습니다")
            else:
                messagebox.showinfo("분석 완료", 
                    f"영상 분석이 완료되었습니다\n\n"
                    f"✅ NSFW 콘텐츠가 탐지되지 않았습니다\n"
                    f"영상이 안전합니다")
            
        except Exception as e:
            messagebox.showerror("분석 오류", f"영상 분석 중 오류가 발생했습니다:\n{e}")
        finally:
            self.progress_bar.stop()
            self.progress_var.set("분석 완료")
            
    def generate_report(self, output_dir, result_info, threshold, total_seconds):
        """분석 보고서 생성"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = os.path.join(output_dir, f"nsfw_analysis_report_{timestamp}.txt")
        
        nsfw_detections = result_info['nsfw_detections']
        original_duration = result_info['original_duration']
        clean_duration = result_info['clean_duration']
        removed_duration = result_info['removed_duration']
        clean_filename = result_info['clean_filename']
        
        with open(report_path, "w", encoding="utf-8") as f:
            f.write("NSFW 영상 분석 및 정화 보고서\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"생성 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"원본 영상 파일: {os.path.basename(self.video_path)}\n")
            f.write(f"원본 영상 길이: {self.format_timestamp(original_duration)}\n")
            f.write(f"분석 임계값: {threshold * 100}%\n")
            f.write(f"분석 프레임 수: {total_seconds}개\n")
            f.write(f"NSFW 탐지 횟수: {len(nsfw_detections)}개\n\n")
            
            f.write("영상 정화 결과:\n")
            f.write("-" * 30 + "\n")
            if clean_filename:
                f.write(f"정화된 영상: {clean_filename}\n")
                f.write(f"정화된 영상 길이: {self.format_timestamp(clean_duration)}\n")
                f.write(f"제거된 시간: {self.format_timestamp(removed_duration)}\n")
                f.write(f"정화율: {(removed_duration/original_duration)*100:.1f}%\n\n")
            else:
                f.write("영상 정화에 실패했습니다\n\n")
            
            if nsfw_detections:
                f.write("탐지된 NSFW 구간 (제거된 구간):\n")
                f.write("-" * 30 + "\n")
                for i, detection in enumerate(nsfw_detections, 1):
                    timestamp = detection['timestamp']
                    confidence = detection['confidence']
                    f.write(f"{i}. {detection['formatted_time']} "
                           f"(신뢰도: {confidence:.1f}%)\n")
                    f.write(f"   제거된 구간: {max(0, timestamp-1):.1f}초 ~ {min(original_duration, timestamp+1):.1f}초\n\n")
            else:
                f.write("✅ 설정된 임계값 이상의 NSFW 콘텐츠가 탐지되지 않았습니다\n")
                
    def show_results(self, result_info, output_dir):
        """결과를 GUI에 표시"""
        self.result_text.delete(1.0, tk.END)
        
        nsfw_detections = result_info['nsfw_detections']
        original_duration = result_info['original_duration']
        clean_duration = result_info['clean_duration']
        removed_duration = result_info['removed_duration']
        clean_filename = result_info['clean_filename']
        
        result_msg = f"분석 및 정화 결과\n"
        result_msg += f"{'='*35}\n\n"
        result_msg += f"🔞 NSFW 탐지 횟수: {len(nsfw_detections)}개\n"
        result_msg += f"결과 저장 위치: {output_dir}\n\n"
        
        result_msg += f"영상 정화 결과:\n"
        result_msg += f"{'-'*25}\n"
        result_msg += f"원본 길이: {self.format_timestamp(original_duration)}\n"
        
        if clean_filename:
            result_msg += f"정화된 길이: {self.format_timestamp(clean_duration)}\n"
            result_msg += f"제거된 시간: {self.format_timestamp(removed_duration)}\n"
            result_msg += f"정화율: {(removed_duration/original_duration)*100:.1f}%\n"
            result_msg += f"📽️ 정화된 영상: {clean_filename}\n\n"
        else:
            result_msg += "영상 정화에 실패했습니다\n\n"
        
        if nsfw_detections:
            result_msg += "제거된 NSFW 구간:\n"
            result_msg += f"{'-'*25}\n"
            for i, detection in enumerate(nsfw_detections, 1):
                timestamp = detection['timestamp']
                confidence = detection['confidence']
                result_msg += f"{i}. {detection['formatted_time']} "
                result_msg += f"({confidence:.1f}%)\n"
                result_msg += f"   제거 구간: {max(0, timestamp-1):.0f}~{min(original_duration, timestamp+1):.0f}초\n\n"
        else:
            result_msg += "✅ 설정된 임계값 이상의 NSFW 콘텐츠가\n"
            result_msg += "   탐지되지 않았습니다"
            
        self.result_text.insert(tk.END, result_msg)
        
    def start_analysis(self):
        """분석 시작"""
        threshold = self.validate_threshold()
        if threshold is None:
            return
            
        if not hasattr(self, 'video_path'):
            messagebox.showwarning("경고", "영상 파일을 선택해주세요")
            return
            
        # 백그라운드에서 분석 실행
        self.analyze_btn.config(state=tk.DISABLED, text="분석 중...")
        analysis_thread = threading.Thread(
            target=lambda: self.analyze_video_wrapper(threshold)
        )
        analysis_thread.daemon = True
        analysis_thread.start()
        
    def analyze_video_wrapper(self, threshold):
        """분석 래퍼 함수"""
        try:
            self.analyze_video(threshold)
        finally:
            # UI 복원
            self.root.after(0, lambda: self.analyze_btn.config(
                state=tk.NORMAL, text="분석 시작"
            ))
            
    def run(self):
        """GUI 실행"""
        self.root.mainloop()

def main():
    """메인 실행 함수"""
    app = NSFWVideoAnalyzerGUI()
    app.run()

if __name__ == "__main__":
    main() 