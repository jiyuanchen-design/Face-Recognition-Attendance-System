import cv2
import numpy as np
import datetime
from config import SIMILARITY_THRESHOLD
from db_manager import DatabaseManager
from face_processor import FaceProcessor

class AttendanceCore:
    def __init__(self):
        self.db = DatabaseManager()
        self.fp = FaceProcessor()
        self.known = []
        self.load()
        self.signed = set()
        self.capture_count = 0
        self.need_capture = 20
        self.capturing = False
        self.mode = "checkin"

    def load(self):
        self.known = []
        for sid, name, bs in self.db.get_all_features():
            feat = np.frombuffer(bs, np.float32)
            self.known.append((sid, name, feat))

    def set_mode(self, mode):
        self.mode = mode
        self.capturing = False
        self.capture_count = 0

    def run(self, bgr):
        face, box = self.fp.detect(bgr)
        if face is None:
            return bgr, "未检测到人脸"

        feat = self.fp.feature(face)
        if feat is None:
            return bgr, "特征提取中"

        best = -1
        who = None
        for sid, name, f in self.known:
            s = self.fp.sim(feat, f)
            if s > best:
                best = s
                who = (sid, name)

        if best > SIMILARITY_THRESHOLD and who:
            sid, name = who
            color = (0, 255, 0)

            if self.mode == "checkin":
                if sid in self.signed:
                    return bgr, f"{name} 已签到"

                if not self.capturing:
                    self.capturing = True
                    self.capture_count = 0

                self.capture_count += 1
                msg = f"{name} 采集中 {self.capture_count}/{self.need_capture}"

                if self.capture_count >= self.need_capture:
                    status = "签到完成"
                    self.db.add_attendance_record(sid, name, status)
                    self.signed.add(sid)
                    self.capturing = False
                    return bgr, f"{name} {status}"

            elif self.mode == "checkout":
                if sid not in self.signed:
                    return bgr, f"{name} 未签到"

                if not self.capturing:
                    self.capturing = True
                    self.capture_count = 0

                self.capture_count += 1
                msg = f"{name} 签退采集中 {self.capture_count}/{self.need_capture}"

                if self.capture_count >= self.need_capture:
                    self.db.add_attendance_record(sid, name, "签退完成")
                    self.signed.discard(sid)
                    self.capturing = False
                    return bgr, f"{name} 签退完成"

            txt = name
        else:
            color = (0, 0, 255)
            txt = "未知"
            msg = "未知人员"

        out = bgr.copy()
        x1, y1, x2, y2 = box
        cv2.rectangle(out, (x1, y1), (x2, y2), color, 2)
        cv2.putText(out, txt, (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,255,255), 2)
        return out, msg