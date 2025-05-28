import os
import warnings
import time
import base64
import tempfile
import tkinter as tk
from tkinter import simpledialog, messagebox
from PIL import Image, ImageTk
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from utils import detect_nsfw_from_image


def show_warning_popup():
    win = tk.Tk()
    win.title("⚠️ 외설 감지")
    win.attributes("-topmost", True)
    win.configure(bg="black")

    screen_width = win.winfo_screenwidth()
    screen_height = win.winfo_screenheight()
    win_width = int(screen_width * 0.6)
    win_height = int(screen_height * 0.6)
    x = (screen_width - win_width) // 2
    y = (screen_height - win_height) // 2
    win.geometry(f"{win_width}x{win_height}+{x}+{y}")

    image_path = os.path.join(os.path.dirname(__file__), "warn.jpg")
    pil_img = Image.open(image_path).resize((win_width, win_height - 100), Image.Resampling.LANCZOS)
    tk_img = ImageTk.PhotoImage(pil_img)

    label_img = tk.Label(win, image=tk_img)
    label_img.image = tk_img
    label_img.pack()

    label_text = tk.Label(win, text="⚠️ 외설 콘텐츠가 식별되었습니다!", fg="red", bg="black", font=("Arial", 20, "bold"))
    label_text.pack(pady=10)

    btn = tk.Button(win, text="확인", font=("Arial", 16), command=win.destroy)
    btn.pack(pady=10)

    win.mainloop()


def youtube_explicit_content_detector():
    # 입력 받기용 팝업
    root = tk.Tk()
    root.withdraw()
    youtube_url = simpledialog.askstring("YouTube URL 입력", "분석할 YouTube URL을 입력하세요:")
    if not youtube_url:
        messagebox.showinfo("입력 없음", "URL이 입력되지 않아 종료합니다.")
        return

    EXPLICIT_THRESHOLD = 70.0

    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    try:
        driver.get(youtube_url)
        video_player = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "video"))
        )

        try:
            fullscreen_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, ".ytp-fullscreen-button"))
            )
            fullscreen_button.click()
            time.sleep(1)
        except:
            print("전체 화면 모드로 전환할 수 없습니다.")

        try:
            play_button = driver.find_element(By.CSS_SELECTOR, ".ytp-play-button")
            if "재생" in play_button.get_attribute("aria-label"):
                play_button.click()
        except:
            pass

        print("외설적인 콘텐츠 감지를 시작합니다...")
        temp_dir = tempfile.mkdtemp()
        explicit_detected = False
        frame_count = 0

        while not explicit_detected:
            time.sleep(0.5)
            frame_path = os.path.join(temp_dir, f"frame_{frame_count}.png")
            data_url = driver.execute_script("""
                const video = arguments[0];
                const rect = video.getBoundingClientRect();
                const canvas = document.createElement("canvas");
                canvas.width = rect.width;
                canvas.height = rect.height;
                const ctx = canvas.getContext("2d");
                ctx.drawImage(video,
                    0, 0, video.videoWidth, video.videoHeight,
                    0, 0, rect.width, rect.height
                );
                return canvas.toDataURL("image/png").split(',')[1];
            """, video_player)

            img_data = base64.b64decode(data_url)
            with open(frame_path, "wb") as f:
                f.write(img_data)

            result = detect_nsfw_from_image(frame_path)
            confidence = result["confidence_percentage"]
            print(f"프레임 {frame_count}: 신뢰도 = {confidence:.2f}% / NSFW = {result['is_nsfw']}")

            if result["is_nsfw"] and confidence >= EXPLICIT_THRESHOLD:
                print(f"⚠️ 외설 콘텐츠 감지됨! ({confidence:.2f}%)")
                #우선 영상을 10초 전으로 되돌림
                driver.execute_script("""
                    const video = document.querySelector('video');
                    if (video) video.currentTime = Math.max(0,video.currentTime-10);
                """)

                time.sleep(1)
                #그리고 영상을 멈춤
                pause_button = driver.find_element(By.CSS_SELECTOR, ".ytp-play-button")
                pause_button.click()

                #그리고 영상의 전체화면을 해제
                driver.execute_script("if (document.fullscreenElement) document.exitFullscreen();")
                time.sleep(2)

                explicit_detected = True

                print("영상이 정지되고 전체화면이 해제되었습니다.")#오류확인용출력

            os.remove(frame_path)
            frame_count += 1

        messagebox.showinfo("종료", "분석을 종료합니다.")

    except Exception as e:
        messagebox.showerror("오류 발생", str(e))
    finally:
        driver.quit()
        try:
            os.rmdir(temp_dir)
        except:
            pass


if __name__ == "__main__":
    youtube_explicit_content_detector()
