import os
# -*- coding: utf-8 -*-
import cv2
import time
import numpy as np
from config import DATA_DIR, CAMERA_ID
from face_processor import FaceProcessor

class DataCollector:
    def __init__(self):
        self.fp = FaceProcessor()

    def collect(self, sid, name, count=20):
        path = os.path.join(DATA_DIR, f"{sid}_{name}")
        os.makedirs(path, exist_ok=True)
        cap = cv2.VideoCapture(CAMERA_ID)
        saved = 0
        frame_count = 0  # 新增帧计数器

        print("开始采集人脸，请正对摄像头...")

        while saved < count:
            ret, frame = cap.read()
            if not ret:
                break

            face, box = self.fp.detect(frame)
            show = frame.copy()

            if face is not None:
                x1, y1, x2, y2 = box
                cv2.rectangle(show, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(show, "检测到人脸", (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

                # 每5帧采集1张，保证速度
                if frame_count % 5 == 0:
                    img_path = os.path.join(path, f"{int(time.time())}_{saved}.jpg")
                    cv2.imwrite(img_path, cv2.cvtColor(face, cv2.COLOR_RGB2BGR))
                    saved += 1
                    print(f"已采集 {saved}/{count} 张")  # 终端实时进度

            frame_count += 1  # 每帧自增
            cv2.putText(show, f"已采集: {saved}/{count}", (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            cv2.imshow("Face Collecting", show)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        cap.release()
        cv2.destroyAllWindows()

        if saved >= count:
            print("✅ 人脸采集完成！")
            return True
        else:
            print("❌ 采集未完成，请重试")
            return False

    def get_avg_feature(self, sid, name):
        path = os.path.join(DATA_DIR, f"{sid}_{name}")
        feats = []
        for f in os.listdir(path):
            if f.endswith(".jpg"):
                img = cv2.imread(os.path.join(path, f))
                img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                feat = self.fp.feature(img_rgb)
                if feat is not None:
                    feats.append(feat)
        if not feats:
            return None
        avg = np.mean(feats, axis=0)
        avg = avg / np.linalg.norm(avg)
        return avg.tobytes()