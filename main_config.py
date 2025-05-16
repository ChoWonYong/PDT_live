#최종본(nudenet) + detect frame 확인(using shutil)

import os
import time
import base64
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from nudenet import NudeDetector
import tempfile
import shutil

# 외설 감지 시 스크린샷 저장 폴더
capture_dir = os.path.join(os.getcwd(), "detected_frames")
if not os.path.exists(capture_dir):
    os.makedirs(capture_dir)

def youtube_explicit_content_detector():
    # NudeNet 분류기 초기화
    classifier = NudeDetector()
    
    # 사용자로부터 YouTube URL 입력받기
    youtube_url = input("YouTube URL을 입력하세요: ")
    
    # 분류 임계값 설정 (0.5 = 50%)
    EXPLICIT_THRESHOLD = 0.7
    
    # Chrome 드라이버 설정
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")  # 창 최대화로 시작
  
    # 최신 버전 ChromeDriver 자동 설치 및 사용
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    try:
        # YouTube 동영상 페이지 접속
        driver.get(youtube_url)
        
        # 동영상 플레이어가 로드될 때까지 대기
        video_player = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "video"))
        )
        
        # 동영상을 전체 화면으로 설정
        try:
            fullscreen_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, ".ytp-fullscreen-button"))
            )
            fullscreen_button.click()
            time.sleep(1)  # 전체 화면 전환 대기
        except:
            print("전체 화면 모드로 전환할 수 없습니다. 일반 모드로 계속합니다.")
        
        # 재생 버튼 클릭 (동영상이 자동 재생되지 않는 경우를 대비)
        try:
            play_button = driver.find_element(By.CSS_SELECTOR, ".ytp-play-button")
            if "재생" in play_button.get_attribute("aria-label"):
                play_button.click()
        except:
            pass  # 이미 재생 중이면 무시
        
        print("외설적인 콘텐츠 감지를 시작합니다...")
        
        # 임시 폴더 생성
        temp_dir = tempfile.mkdtemp()
        
        explicit_detected = False
        frame_count = 0
        
        # 감지 루프
        while not explicit_detected:
            # 매 1초마다 대기 후 비디오 요소 자체를 스크린샷
            time.sleep(0.5)
            # video_player는 초기 로드 시 찾은 <video> 요소입니다.
            frame_path = os.path.join(temp_dir, f"frame_{frame_count}.png")
            # JavaScript로 비디오 요소를 캔버스에 그려 base64 PNG로 반환받기
            data_url = driver.execute_script("""
                var video = arguments[0];
                var canvas = document.createElement('canvas');
                canvas.width = video.videoWidth;
                canvas.height = video.videoHeight;
                var ctx = canvas.getContext('2d');
                ctx.drawImage(video, 0, 0);
                return canvas.toDataURL('image/png').split(',')[1];
            """, video_player)
            # Base64 디코딩하여 파일로 저장
            img_data = base64.b64decode(data_url)
            with open(frame_path, "wb") as f:
                f.write(img_data)
            # 임시 이미지 파일 경로를 사용하여 NudeNet으로 분석
            detections = classifier.detect(frame_path)
            # 탐지된 결과 중의 score 값만 추출하여 가장 높은 값을 외설 점수로 사용
            unsafe_score = max((d["score"] for d in detections), default=0.0) 
            print(f"프레임 {frame_count}: 외설 점수 = {unsafe_score:.4f}")
            # 임계값 초과시 영상 정지
            if unsafe_score > EXPLICIT_THRESHOLD:
                print(f"경고: 외설적인 콘텐츠가 감지되었습니다! (점수: {unsafe_score:.4f})")
                
                # 일시정지 버튼 클릭
                pause_button = driver.find_element(By.CSS_SELECTOR, ".ytp-play-button")
                pause_button.click()
                
                detected_path = os.path.join(capture_dir, f"detected_frame_{frame_count}.png")
                shutil.copy(frame_path, detected_path)
                
                explicit_detected = True
                print("영상이 외설적인 콘텐츠로 인해 정지되었습니다.")
            
            # 임시 파일 삭제
            os.remove(frame_path)
            
            frame_count += 1
        
        # 잠시 대기 후 종료
        input("프로그램을 종료하려면 Enter 키를 누르세요...")
        
    except Exception as e:
        print(f"오류 발생: {e}")
    
    finally:
        # 브라우저 종료
        driver.quit()
        
        # 임시 폴더 정리
        try:
            os.rmdir(temp_dir)
        except:
            pass

if __name__ == "__main__":
    youtube_explicit_content_detector()