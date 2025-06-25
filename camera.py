import time
import os
import cv2
import threading
import signal
import sys

class USBCamera:
    def __init__(self, camera_index=0):
        """初始化USB摄像头"""
        self.camera_index = camera_index
        self.cap = None
        self.recording = False
        self.face_cascade = None
        self.stop_recording = False
        self.headless_mode = self.is_headless()
        self.setup_camera()
        self.setup_face_detection()
    
    def is_headless(self):
        """检测是否为无头模式"""
        try:
            import tkinter
            tkinter.Tk().withdraw()
            return False
        except:
            return True
    
    def setup_camera(self):
        """配置摄像头参数"""
        # 初始化摄像头
        self.cap = cv2.VideoCapture(self.camera_index)
        
        if not self.cap.isOpened():
            raise Exception(f"无法打开摄像头 {self.camera_index}")
        
        # 设置摄像头参数
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
        self.cap.set(cv2.CAP_PROP_FPS, 30)
        
        print(f"USB摄像头已初始化，索引: {self.camera_index}")
    
    def setup_face_detection(self):
        """初始化人脸检测器"""
        try:
            # 加载OpenCV预训练的人脸检测器
            self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
            print("人脸检测器已初始化")
        except Exception as e:
            print(f"人脸检测器初始化失败: {e}")
    
    def detect_faces(self, frame):
        """检测人脸"""
        if self.face_cascade is None:
            return []
        
        # 转换为灰度图像
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # 检测人脸
        faces = self.face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(30, 30)
        )
        
        return faces
    
    def capture_photo(self, filename=None):
        """拍照功能"""
        if filename is None:
            filename = f"photo_{int(time.time())}.jpg"
        
        filepath = os.path.join("/home/Fridemn/Projects/final_homework/camera", filename)
        
        # 拍照
        ret, frame = self.cap.read()
        if ret:
            cv2.imwrite(filepath, frame)
            print(f"照片已保存至: {filepath}")
            return filepath
        else:
            print("拍照失败")
            return None
    
    def start_recording_with_face_detection(self, filename=None, duration=10, detection_interval=5):
        """录像功能with人脸检测 - 检测到人脸时输出1，支持提前停止"""
        if filename is None:
            filename = f"video_face_{int(time.time())}.mp4"
        
        filepath = os.path.join("/home/Fridemn/Projects/final_homework/camera", filename)
        
        # 获取摄像头参数
        fps = int(self.cap.get(cv2.CAP_PROP_FPS))
        width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        # 设置视频编码器
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(filepath, fourcc, fps, (width, height))
        
        print(f"开始录像with人脸检测，持续 {duration} 秒...")
        if self.headless_mode:
            print("无头模式运行，按 Ctrl+C 提前停止录像")
        else:
            print("按 Ctrl+C 或 'q' 键提前停止录像")
        
        start_time = time.time()
        face_detected_once = False  # 记录是否曾检测到人脸
        frame_count = 0
        self.stop_recording = False
        
        # 设置信号处理器
        def signal_handler(sig, frame):
            print("\n收到中断信号，正在停止录像...")
            self.stop_recording = True
        
        signal.signal(signal.SIGINT, signal_handler)
        
        try:
            while (time.time() - start_time < duration) and not self.stop_recording:
                ret, frame = self.cap.read()
                if not ret:
                    print("无法读取摄像头画面")
                    break
                
                # 每隔几帧进行一次人脸检测以提高性能
                if frame_count % detection_interval == 0:
                    faces = self.detect_faces(frame)
                    
                    # 每次检测到人脸都输出1
                    if len(faces) > 0:
                        print("1")
                        face_detected_once = True
                        
                        # 在图像上绘制人脸框
                        for (x, y, w, h) in faces:
                            cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 0, 0), 2)
                
                # 写入视频
                out.write(frame)
                frame_count += 1
                
                # 非无头模式才检查键盘输入
                if not self.headless_mode:
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        print("用户按下 'q' 键，停止录像")
                        break
        
        except KeyboardInterrupt:
            print("\n用户中断，停止录像")
        
        finally:
            out.release()
            if not self.headless_mode:
                cv2.destroyAllWindows()
        
        elapsed_time = time.time() - start_time
        print(f"\n录像已保存至: {filepath}")
        print(f"实际录像时长: {elapsed_time:.1f} 秒")
        if face_detected_once:
            print("录像过程中检测到人脸")
        else:
            print("录像过程中未检测到人脸")
        return filepath
    
    def start_realtime_face_detection(self):
        """实时人脸检测，按键退出"""
        print("开始实时人脸检测...")
        if self.headless_mode:
            print("无头模式运行，按 Ctrl+C 退出")
        else:
            print("按 'q' 键或 Ctrl+C 退出")
        
        face_detected_ever = False  # 记录是否曾检测到人脸
        self.stop_recording = False
        frame_count = 0
        detection_interval = 5  # 每5帧检测一次
        
        def signal_handler(sig, frame):
            print("\n收到中断信号，正在退出...")
            self.stop_recording = True
        
        signal.signal(signal.SIGINT, signal_handler)
        
        try:
            while not self.stop_recording:
                ret, frame = self.cap.read()
                if not ret:
                    print("无法读取摄像头画面")
                    break
                
                # 每隔几帧检测一次人脸
                if frame_count % detection_interval == 0:
                    faces = self.detect_faces(frame)
                    
                    # 每次检测到人脸都输出1
                    if len(faces) > 0:
                        print("1")
                        face_detected_ever = True
                
                # 如果不是无头模式，显示图像
                if not self.headless_mode:
                    # 在图像上绘制人脸框
                    if frame_count % detection_interval == 0:
                        faces = self.detect_faces(frame)
                        if len(faces) > 0:
                            for (x, y, w, h) in faces:
                                cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 0, 0), 2)
                                cv2.putText(frame, 'Face Detected', (x, y-10), 
                                           cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 0, 0), 2)
                    
                    cv2.imshow('Real-time Face Detection', frame)
                    
                    # 检查键盘输入
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        print("用户按下 'q' 键，退出检测")
                        break
                else:
                    # 无头模式下，定期输出检测状态
                    if frame_count % 150 == 0:  # 每150帧输出一次状态
                        current_time = int(time.time())
                        print(f"检测中... 时间: {current_time}")
                
                frame_count += 1
        
        except KeyboardInterrupt:
            print("\n用户中断，退出检测")
        
        finally:
            if not self.headless_mode:
                cv2.destroyAllWindows()
        
        if face_detected_ever:
            print("检测过程中发现人脸")
        else:
            print("检测过程中未发现人脸")

    def capture_photo(self, filename=None):
        """拍照功能"""
        if filename is None:
            filename = f"photo_{int(time.time())}.jpg"
        
        filepath = os.path.join("/home/Fridemn/Projects/final_homework/camera", filename)
        
        # 拍照
        ret, frame = self.cap.read()
        if ret:
            cv2.imwrite(filepath, frame)
            print(f"照片已保存至: {filepath}")
            return filepath
        else:
            print("拍照失败")
            return None
    
    def start_recording(self, filename=None, duration=10):
        """录像功能"""
        if filename is None:
            filename = f"video_{int(time.time())}.mp4"
        
        filepath = os.path.join("/home/Fridemn/Projects/final_homework/camera", filename)
        
        # 获取摄像头参数
        fps = int(self.cap.get(cv2.CAP_PROP_FPS))
        width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        # 设置视频编码器
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(filepath, fourcc, fps, (width, height))
        
        print(f"开始录像，持续 {duration} 秒...")
        start_time = time.time()
        
        while time.time() - start_time < duration:
            ret, frame = self.cap.read()
            if ret:
                out.write(frame)
            else:
                break
        
        out.release()
        print(f"录像已保存至: {filepath}")
        return filepath
    
    def preview_with_face_detection(self, duration=5):
        """预览功能with人脸检测"""
        print(f"开始预览with人脸检测 {duration} 秒...")
        
        start_time = time.time()
        while time.time() - start_time < duration:
            ret, frame = self.cap.read()
            if ret:
                # 检测人脸
                faces = self.detect_faces(frame)
                
                if len(faces) > 0:
                    print("1")  # 检测到人脸时输出1
                    
                    # 在图像上绘制人脸框
                    for (x, y, w, h) in faces:
                        cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 0, 0), 2)
                        cv2.putText(frame, 'Face Detected', (x, y-10), 
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 0, 0), 2)
                
                cv2.imshow('USB Camera Preview - Face Detection', frame)
                
                # 按 'q' 键退出预览
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
            else:
                print("无法读取摄像头画面")
                break
        
        cv2.destroyAllWindows()
        print("预览结束")
    
    def preview_camera(self, duration=5):
        """预览功能"""
        print(f"开始预览 {duration} 秒...")
        
        start_time = time.time()
        while time.time() - start_time < duration:
            ret, frame = self.cap.read()
            if ret:
                cv2.imshow('USB Camera Preview', frame)
                
                # 按 'q' 键退出预览
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
            else:
                print("无法读取摄像头画面")
                break
        
        cv2.destroyAllWindows()
        print("预览结束")
    
    def capture_multiple_photos(self, count=5, interval=2):
        """连续拍照"""
        print(f"开始连续拍照，共 {count} 张，间隔 {interval} 秒")
        
        photos = []
        for i in range(count):
            filename = f"series_{int(time.time())}_{i+1}.jpg"
            filepath = self.capture_photo(filename)
            if filepath:
                photos.append(filepath)
            
            if i < count - 1:  # 最后一张不需要等待
                time.sleep(interval)
        
        print(f"连续拍照完成，共拍摄 {len(photos)} 张照片")
        return photos
    
    def get_camera_info(self):
        """获取摄像头信息"""
        if self.cap is None or not self.cap.isOpened():
            print("摄像头未初始化")
            return
        
        width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = int(self.cap.get(cv2.CAP_PROP_FPS))
        
        print("USB摄像头信息:")
        print(f"  分辨率: {width} x {height}")
        print(f"  帧率: {fps} fps")
        print(f"  摄像头索引: {self.camera_index}")
    
    def list_available_cameras(self):
        """列出可用的摄像头"""
        print("检测可用的摄像头:")
        available_cameras = []
        
        for i in range(10):  # 检测前10个索引
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                available_cameras.append(i)
                print(f"  摄像头 {i}: 可用")
                cap.release()
            else:
                break
        
        if not available_cameras:
            print("  未检测到可用摄像头")
        
        return available_cameras
    
    def cleanup(self):
        """清理资源"""
        if self.cap is not None:
            self.cap.release()
        cv2.destroyAllWindows()
        print("摄像头资源已释放")

def main():
    """主函数示例"""
    print("USB摄像头测试程序 - 带人脸检测功能")
    
    try:
        # 创建摄像头实例
        camera = USBCamera(camera_index=0)
        
        # 获取摄像头信息
        camera.get_camera_info()
        
        if camera.headless_mode:
            print("检测到无头模式环境")
        
        # 等待摄像头稳定
        time.sleep(2)
        
        print("\n选择模式:")
        print("1. 录像with人脸检测 (30秒)")
        print("2. 实时人脸检测")
        
        choice = input("请选择模式 (1 或 2): ").strip()
        
        if choice == "1":
            print("\n开始录像功能with人脸检测...")
            camera.start_recording_with_face_detection("face_detection_video.mp4", 30, detection_interval=3)
        elif choice == "2":
            print("\n开始实时人脸检测...")
            camera.start_realtime_face_detection()
        else:
            print("无效选择，默认使用录像模式")
            camera.start_recording_with_face_detection("face_detection_video.mp4", 30, detection_interval=3)
        
        print("\n程序完成！")
        
    except Exception as e:
        print(f"发生错误: {e}")
    
    finally:
        # 清理资源
        camera.cleanup()

if __name__ == "__main__":
    main()
