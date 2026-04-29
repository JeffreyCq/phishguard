"""
classifier.py — Inferencia ONNX. No requiere PyTorch instalado.
"""

import numpy as np
import onnxruntime as ort
from pathlib import Path
from transformers import DistilBertTokenizerFast

MODEL_DIR = Path(__file__).parent.parent / "model"
ONNX_PATH = MODEL_DIR / "maildefender.onnx"
TOK_PATH  = MODEL_DIR / "tokenizer"
MAX_LEN   = 256


class ThreatClassifier:
    _instance = None  # singleton — carga el modelo una sola vez

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._loaded = False
        return cls._instance

    def _load(self):
        if self._loaded:
            return
        if not ONNX_PATH.exists():
            raise FileNotFoundError(
                f"Model not found at {ONNX_PATH}\n"
                "Run training in Colab and copy maildefender.onnx to ml/model/"
            )
        opts = ort.SessionOptions()
        opts.intra_op_num_threads = 4
        opts.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
        self._session = ort.InferenceSession(str(ONNX_PATH), sess_options=opts)
        self._tokenizer = DistilBertTokenizerFast.from_pretrained(str(TOK_PATH))
        self._loaded = True

    def predict_proba(self, text: str) -> np.ndarray:
        self._load()
        enc = self._tokenizer(
            text,
            return_tensors="np",
            truncation=True,
            padding="max_length",
            max_length=MAX_LEN,
        )
        logits = self._session.run(
            None,
            {"input_ids": enc["input_ids"], "attention_mask": enc["attention_mask"]},
        )[0][0]
        return _softmax(logits)


def _softmax(x: np.ndarray) -> np.ndarray:
    e = np.exp(x - x.max())
    return e / e.sum()
