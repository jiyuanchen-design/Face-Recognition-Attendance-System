import cv2
import numpy as np
import torch
import torchvision.transforms as transforms
from torchvision.models import resnet18, ResNet18_Weights
from config import DEVICE, FACE_SIZE


class FaceProcessor:
    def __init__(self):
        # 加载OpenCV人脸检测器
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

        self.extractor = self._build_extractor()
        self.extractor.to(DEVICE)
        self.extractor.eval()

        self.transform = transforms.Compose([
            transforms.ToPILImage(),
            transforms.Resize(FACE_SIZE),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
        ])

    def _build_extractor(self):
        model = resnet18(weights=ResNet18_Weights.DEFAULT)
        return torch.nn.Sequential(*list(model.children())[:-1])

    def detect(self, bgr):
        gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(gray, 1.1, 4)

        if len(faces) == 0:
            return None, None

        x, y, w, h = faces[0]
        pad = 20
        x1 = max(0, x - pad)
        y1 = max(0, y - pad)
        x2 = min(bgr.shape[1], x + w + pad)
        y2 = min(bgr.shape[0], y + h + pad)

        rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
        return rgb[y1:y2, x1:x2], (x1, y1, x2, y2)

    def feature(self, face):
        if face is None:
            return None

        t = self.transform(face).unsqueeze(0).to(DEVICE)
        with torch.no_grad():
            feat = self.extractor(t).flatten().cpu().numpy()
        return feat / np.linalg.norm(feat)

    @staticmethod
    def sim(a, b):
        return np.dot(a, b)