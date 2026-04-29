# MailDefender — Fine-tuning en Google Colab
# ─────────────────────────────────────────────────────────────────────────────
# INSTRUCCIONES:
#   1. Ve a https://colab.research.google.com
#   2. Nuevo notebook → Runtime → Change runtime type → T4 GPU
#   3. Copia cada bloque de código en una celda separada y ejecútalas en orden
#   4. Sube dataset.csv cuando se lo pida
#   5. Al final descarga maildefender.onnx
# ─────────────────────────────────────────────────────────────────────────────


# ╔══════════════════════════════════════════════════════════╗
# ║  CELDA 1 — Instalar dependencias                        ║
# ╚══════════════════════════════════════════════════════════╝
"""
!pip install -q transformers datasets scikit-learn onnx onnxruntime accelerate
print("✓ Dependencias instaladas")
"""


# ╔══════════════════════════════════════════════════════════╗
# ║  CELDA 2 — Subir dataset.csv                            ║
# ╚══════════════════════════════════════════════════════════╝
"""
from google.colab import files
uploaded = files.upload()   # Selecciona dataset.csv desde tu PC
print("✓ Archivo subido:", list(uploaded.keys()))
"""


# ╔══════════════════════════════════════════════════════════╗
# ║  CELDA 3 — Configuración                                ║
# ╚══════════════════════════════════════════════════════════╝
"""
import pandas as pd
import numpy as np
import torch
import random
import os

# Reproducibilidad
SEED = 42
random.seed(SEED)
np.random.seed(SEED)
torch.manual_seed(SEED)

MODEL_NAME   = "distilbert-base-uncased"
NUM_LABELS   = 5
MAX_LEN      = 256      # 256 tokens = buen balance velocidad/precisión
BATCH_SIZE   = 16
EPOCHS       = 4
LR           = 2e-5
OUTPUT_DIR   = "/content/maildefender_model"
ONNX_PATH    = "/content/maildefender.onnx"

LABEL_NAMES = ["legitimate", "spam", "phishing", "spear_phishing", "whaling"]

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"✓ Usando: {device}")
print(f"  GPU: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'ninguna (CPU)'}")
"""


# ╔══════════════════════════════════════════════════════════╗
# ║  CELDA 4 — Cargar y preparar dataset                    ║
# ╚══════════════════════════════════════════════════════════╝
"""
from sklearn.model_selection import train_test_split
from datasets import Dataset

df = pd.read_csv("dataset.csv")
print(f"Total registros: {len(df)}")
print(df["label_name"].value_counts())

# Split 80/10/10
train_df, temp_df = train_test_split(df, test_size=0.2, stratify=df["label"], random_state=SEED)
val_df,   test_df = train_test_split(temp_df, test_size=0.5, stratify=temp_df["label"], random_state=SEED)

print(f"\nTrain: {len(train_df)} | Val: {len(val_df)} | Test: {len(test_df)}")

train_ds = Dataset.from_pandas(train_df[["text","label"]].reset_index(drop=True))
val_ds   = Dataset.from_pandas(val_df[["text","label"]].reset_index(drop=True))
test_ds  = Dataset.from_pandas(test_df[["text","label"]].reset_index(drop=True))
"""


# ╔══════════════════════════════════════════════════════════╗
# ║  CELDA 5 — Tokenizar                                    ║
# ╚══════════════════════════════════════════════════════════╝
"""
from transformers import DistilBertTokenizerFast

tokenizer = DistilBertTokenizerFast.from_pretrained(MODEL_NAME)

def tokenize_fn(batch):
    return tokenizer(
        batch["text"],
        truncation=True,
        padding="max_length",
        max_length=MAX_LEN
    )

train_ds = train_ds.map(tokenize_fn, batched=True)
val_ds   = val_ds.map(tokenize_fn, batched=True)
test_ds  = test_ds.map(tokenize_fn, batched=True)

train_ds.set_format("torch", columns=["input_ids", "attention_mask", "label"])
val_ds.set_format("torch",   columns=["input_ids", "attention_mask", "label"])
test_ds.set_format("torch",  columns=["input_ids", "attention_mask", "label"])

print("✓ Tokenización completa")
"""


# ╔══════════════════════════════════════════════════════════╗
# ║  CELDA 6 — Modelo y métricas                            ║
# ╚══════════════════════════════════════════════════════════╝
"""
from transformers import DistilBertForSequenceClassification
from sklearn.metrics import accuracy_score, f1_score, classification_report

model = DistilBertForSequenceClassification.from_pretrained(
    MODEL_NAME,
    num_labels=NUM_LABELS,
    id2label={i: n for i, n in enumerate(LABEL_NAMES)},
    label2id={n: i for i, n in enumerate(LABEL_NAMES)},
)
model = model.to(device)

def compute_metrics(eval_pred):
    logits, labels = eval_pred
    preds = np.argmax(logits, axis=-1)
    return {
        "accuracy": accuracy_score(labels, preds),
        "f1_macro": f1_score(labels, preds, average="macro"),
        "f1_weighted": f1_score(labels, preds, average="weighted"),
    }

print(f"✓ Modelo cargado: {sum(p.numel() for p in model.parameters()):,} parámetros")
"""


# ╔══════════════════════════════════════════════════════════╗
# ║  CELDA 7 — Entrenar                                     ║
# ╚══════════════════════════════════════════════════════════╝
"""
from transformers import TrainingArguments, Trainer

training_args = TrainingArguments(
    output_dir=OUTPUT_DIR,
    num_train_epochs=EPOCHS,
    per_device_train_batch_size=BATCH_SIZE,
    per_device_eval_batch_size=32,
    learning_rate=LR,
    warmup_ratio=0.1,
    weight_decay=0.01,
    eval_strategy="epoch",
    save_strategy="epoch",
    load_best_model_at_end=True,
    metric_for_best_model="f1_macro",
    greater_is_better=True,
    logging_steps=50,
    fp16=torch.cuda.is_available(),
    report_to="none",
    seed=SEED,
)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=train_ds,
    eval_dataset=val_ds,
    compute_metrics=compute_metrics,
)

print("⏳ Entrenando... (~30-45 min en T4 GPU)")
trainer.train()
print("✓ Entrenamiento completo")
"""


# ╔══════════════════════════════════════════════════════════╗
# ║  CELDA 8 — Evaluar en test set                          ║
# ╚══════════════════════════════════════════════════════════╝
"""
results = trainer.evaluate(test_ds)
print("\n─── Resultados en Test Set ───")
for k, v in results.items():
    print(f"  {k}: {v:.4f}" if isinstance(v, float) else f"  {k}: {v}")

# Reporte detallado por clase
preds_output = trainer.predict(test_ds)
preds = np.argmax(preds_output.predictions, axis=-1)
labels = preds_output.label_ids

print("\n─── Reporte por clase ───")
print(classification_report(labels, preds, target_names=LABEL_NAMES))
"""


# ╔══════════════════════════════════════════════════════════╗
# ║  CELDA 9 — Guardar modelo + tokenizer                   ║
# ╚══════════════════════════════════════════════════════════╝
"""
trainer.save_model(OUTPUT_DIR)
tokenizer.save_pretrained(OUTPUT_DIR)
print(f"✓ Modelo guardado en: {OUTPUT_DIR}")
"""


# ╔══════════════════════════════════════════════════════════╗
# ║  CELDA 10 — Exportar a ONNX                             ║
# ╚══════════════════════════════════════════════════════════╝
"""
# ONNX = inferencia rápida en CPU sin necesitar PyTorch instalado
from transformers import DistilBertForSequenceClassification, DistilBertTokenizerFast
import torch

model_loaded = DistilBertForSequenceClassification.from_pretrained(OUTPUT_DIR)
tokenizer_loaded = DistilBertTokenizerFast.from_pretrained(OUTPUT_DIR)
model_loaded.eval()

# Input dummy para trazar el grafo
dummy = tokenizer_loaded(
    "Sample email text for export",
    return_tensors="pt",
    max_length=MAX_LEN,
    padding="max_length",
    truncation=True
)

torch.onnx.export(
    model_loaded,
    (dummy["input_ids"], dummy["attention_mask"]),
    ONNX_PATH,
    input_names=["input_ids", "attention_mask"],
    output_names=["logits"],
    dynamic_axes={
        "input_ids":      {0: "batch"},
        "attention_mask": {0: "batch"},
        "logits":         {0: "batch"},
    },
    opset_version=14,
    do_constant_folding=True,
)
print(f"✓ ONNX exportado: {ONNX_PATH}")

import os
size_mb = os.path.getsize(ONNX_PATH) / 1024 / 1024
print(f"  Tamaño: {size_mb:.1f} MB")
"""


# ╔══════════════════════════════════════════════════════════╗
# ║  CELDA 11 — Descargar archivos                          ║
# ╚══════════════════════════════════════════════════════════╝
"""
from google.colab import files
import shutil

# Descarga el modelo ONNX
files.download(ONNX_PATH)

# Descarga el tokenizer (necesario para inferencia local)
shutil.make_archive("/content/tokenizer", "zip", OUTPUT_DIR)
files.download("/content/tokenizer.zip")

print("✓ Descarga iniciada:")
print("  - maildefender.onnx   → ponlo en ml/model/")
print("  - tokenizer.zip       → extráelo en ml/model/tokenizer/")
"""
