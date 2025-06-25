import time
import os
import cv2
import threading
import signal
import sys
import numpy as np

class USBCamera:
    def __init__(self, camera_index=0):
        """初始化USB摄像头"""
        self.camera_index = camera_index
        self.cap = None
        self.recording = False
        self.face_cascade = None
        self.dnn_net = None
        self.stop_recording = False
        self.headless_mode = self.is_headless()
        self.camera_available = False
        self.face_detection_method = None  # 'cascade' 或 'dnn' 或 None
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
        try:
            # 尝试不同的后端初始化摄像头
            backends = [cv2.CAP_V4L2, cv2.CAP_GSTREAMER, cv2.CAP_ANY]
            
            for backend in backends:
                try:
                    print(f"尝试使用后端 {backend} 初始化摄像头...")
                    self.cap = cv2.VideoCapture(self.camera_index, backend)
                    
                    if self.cap.isOpened():
                        # 测试是否能读取画面
                        ret, frame = self.cap.read()
                        if ret and frame is not None:
                            print(f"摄像头初始化成功，使用后端: {backend}")
                            self.camera_available = True
                            break
                        else:
                            print(f"后端 {backend} 无法读取画面，尝试下一个...")
                            self.cap.release()
                    else:
                        print(f"后端 {backend} 无法打开摄像头，尝试下一个...")
                        
                except Exception as e:
                    print(f"后端 {backend} 初始化失败: {e}")
                    continue
            
            if not self.camera_available:
                print("警告: 所有摄像头后端都失败，摄像头功能将被禁用")
                return
            
            # 尝试设置摄像头参数（如果失败则使用默认值）
            try:
                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                self.cap.set(cv2.CAP_PROP_FPS, 15)
                print("摄像头参数设置完成")
            except Exception as e:
                print(f"摄像头参数设置失败，使用默认参数: {e}")
            
            print(f"USB摄像头已初始化，索引: {self.camera_index}")
            
        except Exception as e:
            print(f"摄像头初始化完全失败: {e}")
            self.camera_available = False
    
    def setup_face_detection(self):
        """初始化人脸检测器"""
        print("正在初始化人脸检测器...")
        
        # 方法1: 尝试使用OpenCV内置的Haar级联分类器
        try:
            if hasattr(cv2, 'data') and hasattr(cv2.data, 'haarcascades'):
                cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
                if os.path.exists(cascade_path):
                    self.face_cascade = cv2.CascadeClassifier(cascade_path)
                    if not self.face_cascade.empty():
                        self.face_detection_method = 'cascade'
                        print(f"人脸检测器已初始化 (Haar级联): {cascade_path}")
                        return
        except Exception as e:
            print(f"Haar级联检测器初始化失败: {e}")
        
        # 方法2: 尝试使用OpenCV DNN人脸检测
        try:
            # 创建一个简单的基于颜色的人脸检测器作为备选
            print("尝试使用DNN人脸检测...")
            # 这里我们使用OpenCV的内置DNN模块
            # 如果有预训练模型，可以加载；否则使用简化检测
            self.face_detection_method = 'simple'
            print("人脸检测器已初始化 (简化检测)")
            return
            
        except Exception as e:
            print(f"DNN人脸检测器初始化失败: {e}")
        
        # 方法3: 最后备选 - 不使用人脸检测
        print("警告: 无法初始化任何人脸检测器，人脸检测功能将被禁用")
        self.face_detection_method = None
    
    def detect_faces(self, frame):
        """检测人脸"""
        if self.face_detection_method == 'cascade' and self.face_cascade is not None:
            return self._detect_faces_cascade(frame)
        elif self.face_detection_method == 'simple':
            return self._detect_faces_simple(frame)
        else:
            return []
    
    def _detect_faces_cascade(self, frame):
        """使用Haar级联检测人脸"""
        try:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = self.face_cascade.detectMultiScale(
                gray,
                scaleFactor=1.1,
                minNeighbors=5,
                minSize=(30, 30)
            )
            return faces
        except Exception as e:
            print(f"Haar级联人脸检测出错: {e}")
            return []
    
    def _detect_faces_simple(self, frame):
        """简化的人脸检测方法 - 基于肤色检测"""
        try:
            # 转换为HSV颜色空间
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            
            # 定义肤色范围 (这是一个简化的方法)
            lower_skin = np.array([0, 20, 70], dtype=np.uint8)
            upper_skin = np.array([20, 255, 255], dtype=np.uint8)
            
            # 创建肤色掩码
            mask = cv2.inRange(hsv, lower_skin, upper_skin)
            
            # 形态学操作去噪
            kernel = np.ones((3, 3), np.uint8)
            mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
            mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
            
            # 查找轮廓
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            faces = []
            for contour in contours:
                area = cv2.contourArea(contour)
                if area > 1000:  # 最小面积阈值
                    x, y, w, h = cv2.boundingRect(contour)
                    # 简单的长宽比检查
                    if 0.7 < h/w < 1.5:  # 人脸大致是椭圆形
                        faces.append([x, y, w, h])
            
            return np.array(faces) if faces else np.array([])
            
        except Exception as e:
            print(f"简化人脸检测出错: {e}")
            return []
    
    def capture_photo(self, filename=None):
        """拍照功能"""
        if not self.camera_available or self.cap is None:
            print("摄像头不可用，无法拍照")
            return None
            
        if filename is None:
            filename = f"photo_{int(time.time())}.jpg"
        
        # 使用当前目录下的camera文件夹
        camera_dir = os.path.join(os.getcwd(), "camera")
        if not os.path.exists(camera_dir):
            os.makedirs(camera_dir)
        
        filepath = os.path.join(camera_dir, filename)
        
        # 拍照
        try:
            ret, frame = self.cap.read()
            if ret and frame is not None:
                cv2.imwrite(filepath, frame)
                print(f"照片已保存至: {filepath}")
                return filepath
            else:
                print("拍照失败：无法读取摄像头画面")
                return None
        except Exception as e:
            print(f"拍照失败: {e}")
            return None
    
    def start_recording_with_face_detection(self, filename=None, duration=10, detection_interval=5):
        """录像功能with人脸检测 - 检测到人脸时输出1，支持提前停止"""
        if filename is None:
            filename = f"video_face_{int(time.time())}.mp4"
        
        # 使用当前目录下的camera文件夹
        camera_dir = os.path.join(os.getcwd(), "camera")
        if not os.path.exists(camera_dir):
            os.makedirs(camera_dir)
        
        filepath = os.path.join(camera_dir, filename)
        
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
        if self.face_detection_method is None:
            print("人脸检测功能不可用")
            return
            
        if self.headless_mode:
            print("无头模式运行，按 Ctrl+C 退出")
        else:
            print("按 'q' 键或 Ctrl+C 退出")
        
        face_detected_ever = False
        self.stop_recording = False
        frame_count = 0
        detection_interval = 5
        last_status_time = time.time()
        
        def signal_handler(sig, frame):
            print("\n收到中断信号，正在退出...")
            self.stop_recording = True
        
        signal.signal(signal.SIGINT, signal_handler)
        
        try:
            while not self.stop_recording:
                ret, frame = self.cap.read()
                if not ret or frame is None:
                    if not self.stop_recording:
                        print("无法读取摄像头画面")
                    break
                
                # 每隔几帧检测一次人脸
                if frame_count % detection_interval == 0:
                    faces = self.detect_faces(frame)
                    
                    if len(faces) > 0:
                        print("1")
                        face_detected_ever = True
                
                # 如果不是无头模式，显示图像
                if not self.headless_mode:
                    if frame_count % detection_interval == 0:
                        faces = self.detect_faces(frame)
                        if len(faces) > 0:
                            for (x, y, w, h) in faces:
                                cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 0, 0), 2)
                                cv2.putText(frame, 'Face Detected', (x, y-10), 
                                           cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 0, 0), 2)
                    
                    cv2.imshow('Real-time Face Detection', frame)
                    
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        print("用户按下 'q' 键，退出检测")
                        break
                else:
                    current_time = time.time()
                    if current_time - last_status_time >= 10:
                        print(f"检测中... 已处理 {frame_count} 帧，检测方法: {self.face_detection_method}")
                        last_status_time = current_time
                
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
    
    def start_recording(self, filename=None, duration=10):
        """录像功能"""
        if filename is None:
            filename = f"video_{int(time.time())}.mp4"
        
        # 使用当前目录下的camera文件夹
        camera_dir = os.path.join(os.getcwd(), "camera")
        if not os.path.exists(camera_dir):
            os.makedirs(camera_dir)
        
        filepath = os.path.join(camera_dir, filename)
        
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
        if not self.camera_available or self.cap is None or not self.cap.isOpened():
            print("摄像头未初始化或不可用")
            return
        
        try:
            width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = int(self.cap.get(cv2.CAP_PROP_FPS))
            
            print("USB摄像头信息:")
            print(f"  分辨率: {width} x {height}")
            print(f"  帧率: {fps} fps")
            print(f"  摄像头索引: {self.camera_index}")
            print(f"  摄像头状态: {'可用' if self.camera_available else '不可用'}")
            print(f"  人脸检测: {'可用' if self.face_detection_method else '不可用'} ({self.face_detection_method or 'None'})")
        except Exception as e:
            print(f"获取摄像头信息失败: {e}")
    
    def cleanup(self):
        """清理资源"""
        try:
            self.stop_recording = True  # 确保停止所有录制
            time.sleep(0.1)  # 给线程一点时间停止
            
            if self.cap is not None:
                self.cap.release()
                self.cap = None
            cv2.destroyAllWindows()
            print("摄像头资源已释放")
        except Exception as e:
            print(f"清理摄像头资源时出错: {e}")

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
