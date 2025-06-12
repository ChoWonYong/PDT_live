#실시간 탐지 방법 

import time
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from datetime import datetime
from PIL import Image
import timm
import torch
import threading
import tkinter as tk
from tkinter import messagebox

class YouTubeNSFWRealTimeDetector:
    def __init__(self, nsfw_threshold=0.5):
        """
        YouTube 실시간 NSFW 탐지 클래스
        
        Args:
            nsfw_threshold (float): NSFW 판별 임계값 (0~1)
        """
        self.nsfw_threshold = nsfw_threshold
        self.user_driver = None  # 사용자가 보는 정상 속도 영상
        self.bg_driver = None    # 백그라운드 2배속 영상 (NSFW 탐지용)
        self.model = None
        self.transforms = None
        self.detection_active = True
        self.nsfw_detected = False
        self.detected_time = 0
        self.stop_target_time = 0  # 사용자 영상이 정지되어야 할 시간
        
        self.setup_nsfw_model()
        print(f"실시간 NSFW 탐지기 초기화 완료")
        print(f"NSFW 임계값: {nsfw_threshold * 100}%")
    
    def setup_nsfw_model(self):
        """NSFW 탐지 모델 초기화"""
        try:
            print("NSFW 탐지 모델 로딩 중...")
            self.model = timm.create_model("hf_hub:Marqo/nsfw-image-detection-384", pretrained=True)
            self.model = self.model.eval()
            
            data_config = timm.data.resolve_model_data_config(self.model)
            self.transforms = timm.data.create_transform(**data_config, is_training=False)
            
            print("NSFW 모델 로딩 완료")
        except Exception as e:
            print(f"NSFW 모델 로딩 실패: {e}")
            raise
    
    def setup_user_driver(self):
        """사용자용 정상 속도 브라우저 설정"""
        chrome_options = Options()
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--start-maximized")  # 최대화 시작
        
        try:
            self.user_driver = webdriver.Chrome(options=chrome_options)
            # 브라우저 최대화
            self.user_driver.maximize_window()
            print("사용자용 브라우저 초기화 완료 (최대화)")
            return True
        except Exception as e:
            print(f"사용자용 브라우저 초기화 실패: {e}")
            return False
    
    def setup_background_driver(self):
        """백그라운드 2배속 브라우저 설정 (숨김)"""
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # 화면에 보이지 않음
        chrome_options.add_argument("--mute-audio")  # 소리 없음
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1280,720")
        
        try:
            self.bg_driver = webdriver.Chrome(options=chrome_options)
            print("백그라운드 브라우저 초기화 완료")
            return True
        except Exception as e:
            print(f"백그라운드 브라우저 초기화 실패: {e}")
            return False
    
    def predict_nsfw_frame(self, image_path):
        """프레임 NSFW 탐지"""
        try:
            img = Image.open(image_path).convert('RGB')
            
            with torch.no_grad():
                output = self.model(self.transforms(img).unsqueeze(0)).softmax(dim=-1).cpu()
            
            probabilities = output[0]
            nsfw_prob = float(probabilities[0])
            sfw_prob = float(probabilities[1])
            
            is_nsfw = nsfw_prob >= self.nsfw_threshold
            
            return {
                'nsfw_probability': nsfw_prob,
                'sfw_probability': sfw_prob,
                'is_nsfw': is_nsfw,
                'confidence': nsfw_prob * 100
            }
        except Exception as e:
            print(f"프레임 분석 오류: {e}")
            return None
    
    def start_user_video(self, youtube_url):
        """사용자용 정상 속도 영상 시작"""
        try:
            print("사용자용 영상 로딩 중...")
            self.user_driver.get(youtube_url)
            time.sleep(3)
            
            # YouTube 비디오 요소 찾기
            video_element = WebDriverWait(self.user_driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "video.html5-main-video"))
            )
            
            # 영상 재생
            self.user_driver.execute_script("""
                var video = arguments[0];
                video.play();
            """, video_element)
            
            print("사용자용 영상 재생 시작 (정상 속도)")
            return video_element
            
        except Exception as e:
            print(f"사용자용 영상 시작 실패: {e}")
            return None
    
    def start_background_video(self, youtube_url):
        """백그라운드 2배속 영상 시작"""
        try:
            print("🔍 백그라운드 영상 로딩 중...")
            self.bg_driver.get(youtube_url)
            time.sleep(3)
            
            # YouTube 비디오 요소 찾기
            video_element = WebDriverWait(self.bg_driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "video.html5-main-video"))
            )
            
            # 영상을 2배속으로 설정하고 음소거 후 재생
            self.bg_driver.execute_script("""
                var video = arguments[0];
                video.playbackRate = 2.0;  // 2배속
                video.muted = true;        // 음소거
                video.play();
            """, video_element)
            
            print("백그라운드 영상 재생 시작 (2배속, 숨김)")
            return video_element
            
        except Exception as e:
            print(f"백그라운드 영상 시작 실패: {e}")
            return None
    
    def nsfw_detection_loop(self, bg_video_element):
        """백그라운드에서 NSFW 탐지를 수행하는 루프"""
        frame_count = 0
        
        print("실시간 NSFW 탐지 시작 (0.5초 간격)")
        print("=" * 50)
        
        while self.detection_active and not self.nsfw_detected:
            try:
                # 현재 재생 시간 확인 (2배속이므로 실제 영상 시간)
                current_time = self.bg_driver.execute_script("""
                    return arguments[0].currentTime;
                """, bg_video_element)
                
                # 프레임 캡처
                timestamp = datetime.now().strftime("%H%M%S_%f")[:-3]
                filename = f"frame_{frame_count:04d}_{current_time:.1f}s_{timestamp}.png"
                filepath = filename
                
                self.bg_driver.save_screenshot(filepath)
                frame_count += 1
                
                # NSFW 분석
                result = self.predict_nsfw_frame(filepath)
                
                if result:
                    confidence = result['confidence']
                    is_nsfw = result['is_nsfw']
                    
                    status = "🔞 NSFW" if is_nsfw else "✅ SAFE"
                    print(f"[{current_time:6.1f}s] {status} | 신뢰도: {confidence:5.1f}%")
                    
                    if is_nsfw:
                        self.nsfw_detected = True
                        self.detected_time = current_time
                        self.stop_target_time = max(0, current_time - 3)  # 2초 전에 정지
                        
                        print(f"\n NSFW 콘텐츠 탐지")
                        print(f"탐지 시간: {current_time:.1f}초")
                        print(f"신뢰도: {confidence:.1f}%")
                        print(f"사용자 영상 정지 예정 시간: {self.stop_target_time:.1f}초")
                        
                        # 프레임 저장 (증거용)
                        evidence_filename = f"NSFW_detected_{current_time:.1f}s_{confidence:.1f}percent.png"
                        os.rename(filepath, evidence_filename)
                        print(f"증거 프레임 저장: {evidence_filename}")
                        
                        break
                
                # 임시 파일 삭제
                if os.path.exists(filepath):
                    os.remove(filepath)
                
                time.sleep(0.5)  # 0.5초 간격
                
            except Exception as e:
                print(f"탐지 루프 오류: {e}")
                time.sleep(0.5)
                continue
        
        print("NSFW 탐지 루프 종료")
    
    def monitor_user_video(self, user_video_element, bg_video_element):
        """사용자 영상을 실시간 모니터링하여 정지 시점에서 자동 정지"""
        print("사용자 영상 실시간 모니터링 시작...")
        
        while self.detection_active:
            try:
                if self.nsfw_detected:
                    # 현재 사용자 영상 재생 시간 확인
                    current_user_time = self.user_driver.execute_script("""
                        return arguments[0].currentTime;
                    """, user_video_element)
                    
                    # 정지 시점에 도달하면 즉시 정지
                    if current_user_time >= self.stop_target_time:
                        # 사용자 영상 정지 (브라우저 닫지 않음)
                        self.user_driver.execute_script("""
                            arguments[0].pause();
                        """, user_video_element)
                        
                        # 백그라운드 영상도 정지 및 백그라운드 처리 중단
                        self.bg_driver.execute_script("""
                            arguments[0].pause();
                        """, bg_video_element)
                        
                        print(f"사용자 영상 정지 (실제 시간: {current_user_time:.1f}초)")
                        print(f"백그라운드 처리 중단")
                        # print(f"브라우저는 열린 상태로 유지됩니다")
                        
                        self.detection_active = False  # 모든 백그라운드 처리 종료
                        break
                        
                time.sleep(0.1)  # 0.1초마다 체크
                
            except Exception as e:
                print(f"사용자 영상 모니터링 오류: {e}")
                time.sleep(0.1)
                continue
        
        print("사용자 영상 모니터링 종료")
    
    def stop_videos(self, user_video_element, bg_video_element, stop_time):
        """두 영상 모두 정지"""
        try:
            # 사용자 영상을 지정된 시간에서 정지
            self.user_driver.execute_script(f"""
                var video = arguments[0];
                video.currentTime = {stop_time};
                video.pause();
            """, user_video_element)
            
            # 백그라운드 영상 정지
            self.bg_driver.execute_script("""
                var video = arguments[0];
                video.pause();
            """, bg_video_element)
            
            print(f"영상 정지 완료 (사용자 영상: {stop_time:.1f}초에서 정지)")
            
        except Exception as e:
            print(f"영상 정지 오류: {e}")
    
    def run_detection(self, youtube_url):
        """메인 탐지 실행"""
        # 브라우저 초기화
        if not self.setup_user_driver():
            return False
        
        if not self.setup_background_driver():
            return False
        
        try:
            print("\n 영상 실행 시작...")
            
            # 1단계: 백그라운드 영상 먼저 시작
            print(" 백그라운드 탐지 시스템 시작...")
            bg_video = self.start_background_video(youtube_url)
            if not bg_video:
                return False
            
            # 2단계: 사용자 영상 시작 (약간의 딜레이 후)
            time.sleep(0.5)  # 백그라운드가 먼저 시작되도록
            print(" 사용자 영상 시작 (최대화)...")
            user_video = self.start_user_video(youtube_url)
            if not user_video:
                return False
            
            # 백그라운드에서 NSFW 탐지 시작
            detection_thread = threading.Thread(
                target=self.nsfw_detection_loop,
                args=(bg_video,)
            )
            detection_thread.daemon = True
            detection_thread.start()
            
            # 사용자 영상 실시간 모니터링 시작
            monitor_thread = threading.Thread(
                target=self.monitor_user_video,
                args=(user_video, bg_video)
            )
            monitor_thread.daemon = True
            monitor_thread.start()
            
            print("\n 사용자 영상 재생 중 (최대화 화면)...")
            print("백그라운드에서 고속 NSFW 탐지 중...")
            print("실시간 정지 시점 모니터링 중...")
            print("종료하려면 Ctrl+C를 누르세요")
            
            # 탐지 결과 대기
            while self.detection_active and not self.nsfw_detected:
                time.sleep(0.1)
                
                # 영상이 끝났는지 확인
                try:
                    ended = self.user_driver.execute_script("""
                        return arguments[0].ended;
                    """, user_video)
                    
                    if ended:
                        print("영상이 정상적으로 끝났습니다")
                        break
                        
                except:
                    pass
            
            # NSFW 탐지 시 모니터링이 자동으로 정지 처리
            if self.nsfw_detected:
                print(f"\n 외설적 콘텐츠 탐지로 인한 영상 정지 대기 중...")
                print(f" 백그라운드 탐지 시간: {self.detected_time:.1f}초")
                print(f" 사용자 영상이 {self.stop_target_time:.1f}초에 도달하면 자동 정지됩니다")
                
                # 모니터링 스레드가 정지할 때까지 대기
                while self.detection_active and self.nsfw_detected:
                    time.sleep(0.1)
                    
                # print(f"\n 영상 정지 완료. 브라우저를 수동으로 닫으세요")
                print(f"정지된 시간: {self.stop_target_time:.1f}초")
                
                # 사용자가 브라우저를 닫을 때까지 대기
                input("\n  Enter 키를 누르면 프로그램을 종료합니다...")
                    
                return True
            
            return True
            
        except KeyboardInterrupt:
            print("\n 사용자에 의해 중단됨")
            return True
        except Exception as e:
            print(f"\n 실행 중 오류: {e}")
            return False
    
    def close(self):
        """리소스 정리 (NSFW 탐지 시에는 브라우저 유지)"""
        self.detection_active = False
        
        # NSFW가 탐지된 경우 브라우저를 열린 상태로 유지
        if not self.nsfw_detected:
            if self.user_driver:
                try:
                    self.user_driver.quit()
                    print("사용자 브라우저 종료")
                except:
                    pass
            
            if self.bg_driver:
                try:
                    self.bg_driver.quit()
                    print("백그라운드 브라우저 종료")
                except:
                    pass
        else:
            # NSFW 탐지 시에는 백그라운드 브라우저만 종료
            if self.bg_driver:
                try:
                    self.bg_driver.quit()
                    print("백그라운드 브라우저 종료")
                except:
                    pass
            print("사용자 브라우저는 열린 상태로 유지됩니다")

class YouTubeAnalyzerGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("YouTube 실시간 NSFW 탐지기")
        self.root.geometry("500x300")
        self.root.resizable(False, False)
        
        # 창을 화면 중앙에 배치
        self.center_window()
        
        self.detector = None
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
        from tkinter import ttk
        
        # 메인 프레임
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 제목
        title_label = ttk.Label(main_frame, text="🎬 YouTube 실시간 NSFW 탐지기", 
                               font=("Arial", 16, "bold"))
        title_label.pack(pady=(0, 20))
        
        # YouTube URL 입력 섹션
        url_frame = ttk.LabelFrame(main_frame, text="YouTube URL", padding="10")
        url_frame.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Label(url_frame, text="YouTube URL을 입력하세요:", 
                 font=("Arial", 10)).pack(anchor=tk.W)
        
        self.url_var = tk.StringVar()
        url_entry = ttk.Entry(url_frame, textvariable=self.url_var, 
                             font=("Arial", 10), width=50)
        url_entry.pack(fill=tk.X, pady=(5, 0))
        
        # Threshold 입력 섹션
        threshold_frame = ttk.LabelFrame(main_frame, text="NSFW 탐지 민감도", padding="10")
        threshold_frame.pack(fill=tk.X, pady=(0, 20))
        
        ttk.Label(threshold_frame, text="NSFW 탐지 임계값 (0~100):", 
                 font=("Arial", 10)).pack(anchor=tk.W)
        
        self.threshold_var = tk.StringVar(value="50")
        threshold_entry = ttk.Entry(threshold_frame, textvariable=self.threshold_var, 
                                   font=("Arial", 10), width=10)
        threshold_entry.pack(anchor=tk.W, pady=(5, 0))
        
        # 분석 시작 버튼
        self.start_btn = ttk.Button(main_frame, text="🚀 실시간 분석 시작", 
                                   command=self.start_analysis)
        self.start_btn.pack(pady=10)
        
        # 정보 텍스트
        info_text = ttk.Label(main_frame, 
                             text="• 백그라운드에서 2배속으로 NSFW를 미리 탐지합니다\n"
                                  "• NSFW 탐지 시 사용자 영상이 자동으로 정지됩니다\n"
                                  "• 영상은 최대화 창에서 재생됩니다",
                             font=("Arial", 9), foreground="gray", justify=tk.LEFT)
        info_text.pack(pady=(10, 0))
        
    def validate_inputs(self):
        """입력값 검증"""
        # URL 검증
        url = self.url_var.get().strip()
        if not url:
            messagebox.showerror("입력 오류", "YouTube URL을 입력해주세요")
            return None, None
            
        if "youtube.com" not in url and "youtu.be" not in url:
            messagebox.showerror("입력 오류", "올바른 YouTube URL을 입력해주세요")
            return None, None
            
        # Threshold 검증
        try:
            threshold = float(self.threshold_var.get())
            if not (0 <= threshold <= 100):
                raise ValueError()
            threshold = threshold / 100.0  # 0~1 범위로 변환
        except ValueError:
            messagebox.showerror("입력 오류", "임계값은 0~100 사이의 숫자여야 합니다")
            return None, None
            
        return url, threshold
        
    def start_analysis(self):
        """분석 시작"""
        url, threshold = self.validate_inputs()
        if url is None or threshold is None:
            return
            
        # GUI 닫기
        self.root.destroy()
        
        print(f"\n 설정된 임계값: {threshold * 100}%")
        print(f"YouTube URL: {url}")
        print("\n 실시간 분석을 시작합니다...")
        
        # 탐지기 실행
        detector = YouTubeNSFWRealTimeDetector(nsfw_threshold=threshold)
        
        try:
            detector.run_detection(url)
        finally:
            detector.close()
        
    def run(self):
        """GUI 실행"""
        self.root.mainloop()

def main():
    """메인 실행 함수"""
    import tkinter as tk
    from tkinter import messagebox
    
    print("🎬 YouTube 실시간 NSFW 탐지기 GUI 시작")
    
    try:
        app = YouTubeAnalyzerGUI()
        app.run()
    except Exception as e:
        print(f"실행 오류: {e}")
        if 'app' in locals():
            messagebox.showerror("실행 오류", f"분석 중 오류가 발생했습니다:\n{e}")

if __name__ == "__main__":
    main() 