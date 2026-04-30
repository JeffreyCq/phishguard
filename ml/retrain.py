#!/usr/bin/env python3
"""
MailDefender retraining script — periodic fine-tuning from user feedback.

What it does:
  1. Load corrected feedback from SQLite (scans where user said verdict was wrong)
  2. Load original dataset.csv as replay buffer (prevents catastrophic forgetting)
  3. Combine datasets and fine-tune DistilBERT from last checkpoint
  4. Evaluate accuracy on held-out split — abort if below threshold
  5. Export validated model to ONNX
  6. Optionally auto-swap production model

Usage:
  python retrain.py \\
    --db /data/maildefender.db \\
    --dataset ml/data/processed/dataset.csv \\
    --checkpoint ml/model/tokenizer \\
    --output ml/model/maildefender_new.onnx \\
    --min-feedback 50 \\
    --epochs 3

  # Auto-swap after validation:
  python retrain.py ... --auto-swap

  # Call ML service /reload after swap:
  curl -X POST https://ml.maildefender.xyz/reload
"""

import argparse
import sqlite3
import sys
import shutil
from pathlib import Path

import numpy as np
import pandas as pd

LABEL_MAP = {
    "legitimate":     0,
    "spam":           1,
    "phishing":       2,
    "spear_phishing": 3,
    "whaling":        4,
}
ID_TO_LABEL = {v: k for k, v in LABEL_MAP.items()}
MIN_ACCURACY = 0.85


# ── Data loading ──────────────────────────────────────────────────────────────

def load_feedback(db_path: str, min_samples: int) -> pd.DataFrame | None:
    conn = sqlite3.connect(db_path)
    df = pd.read_sql_query(
        """
        SELECT s.subject, s.sender, s.body_text, f.true_label
        FROM   feedback f
        JOIN   scans s ON f.scan_id = s.scan_id
        WHERE  f.is_correct = 0
          AND  f.true_label IS NOT NULL
          AND  s.body_text  IS NOT NULL
          AND  s.body_text  != ''
        """,
        conn,
    )
    conn.close()

    df = df[df["true_label"].isin(LABEL_MAP)].copy()
    print(f"Feedback samples: {len(df)}")
    print(f"  Distribution: {df['true_label'].value_counts().to_dict()}")

    if len(df) < min_samples:
        print(
            f"\nNeed at least {min_samples} corrected samples to retrain. "
            f"Currently have {len(df)}.\n"
            "Use --min-feedback 1 to force retrain (not recommended below 50 samples)."
        )
        return None

    df["text"]  = (df["subject"].fillna("") + " " + df["body_text"].fillna("")).str.strip()
    df["label"] = df["true_label"].map(LABEL_MAP)
    return df[["text", "label"]].dropna()


def load_original_dataset(dataset_path: str) -> pd.DataFrame:
    df = pd.read_csv(dataset_path)
    if "label" not in df.columns and "label_name" in df.columns:
        df["label"] = df["label_name"].map(LABEL_MAP)
    df = df[["text", "label"]].dropna()
    print(f"Original dataset: {len(df)} samples")
    return df


# ── Training + ONNX export ────────────────────────────────────────────────────

def train_and_export(
    combined_df: pd.DataFrame,
    checkpoint_path: str,
    output_path: str,
    epochs: int,
) -> float:
    import torch
    from transformers import (
        DistilBertTokenizerFast,
        DistilBertForSequenceClassification,
        Trainer,
        TrainingArguments,
    )
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import accuracy_score
    from datasets import Dataset

    print(f"\nCombined training set: {len(combined_df)} samples")
    print(f"  Distribution: {combined_df['label'].value_counts().to_dict()}")

    train_df, eval_df = train_test_split(
        combined_df, test_size=0.10, stratify=combined_df["label"], random_state=42
    )

    tokenizer = DistilBertTokenizerFast.from_pretrained(checkpoint_path)

    def tokenize(batch):
        return tokenizer(
            batch["text"], truncation=True, max_length=256, padding="max_length"
        )

    train_ds = (
        Dataset.from_pandas(train_df.reset_index(drop=True))
        .map(tokenize, batched=True)
        .rename_column("label", "labels")
        .with_format("torch")
    )
    eval_ds = (
        Dataset.from_pandas(eval_df.reset_index(drop=True))
        .map(tokenize, batched=True)
        .rename_column("label", "labels")
        .with_format("torch")
    )

    model = DistilBertForSequenceClassification.from_pretrained(
        checkpoint_path,
        num_labels=5,
        id2label=ID_TO_LABEL,
        label2id=LABEL_MAP,
        ignore_mismatched_sizes=True,
    )

    args = TrainingArguments(
        output_dir="./retrain_checkpoints",
        num_train_epochs=epochs,
        per_device_train_batch_size=16,
        per_device_eval_batch_size=32,
        eval_strategy="epoch",
        save_strategy="epoch",
        load_best_model_at_end=True,
        metric_for_best_model="accuracy",
        learning_rate=2e-5,
        weight_decay=0.01,
        logging_steps=50,
        report_to="none",
    )

    def compute_metrics(eval_pred):
        logits, labels = eval_pred
        preds = np.argmax(logits, axis=1)
        return {"accuracy": accuracy_score(labels, preds)}

    trainer = Trainer(
        model=model,
        args=args,
        train_dataset=train_ds,
        eval_dataset=eval_ds,
        compute_metrics=compute_metrics,
    )

    print("\nStarting fine-tuning...")
    trainer.train()

    metrics  = trainer.evaluate()
    accuracy = metrics.get("eval_accuracy", 0.0)
    print(f"\nEval accuracy: {accuracy:.4f}")

    if accuracy < MIN_ACCURACY:
        print(
            f"\nAccuracy {accuracy:.4f} is below minimum threshold {MIN_ACCURACY}. "
            "ONNX export aborted — production model unchanged."
        )
        sys.exit(1)

    # Export to ONNX
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    print(f"\nExporting to ONNX: {output_path}")

    model.eval()
    dummy = tokenizer(
        "test email",
        return_tensors="pt",
        max_length=256,
        truncation=True,
        padding="max_length",
    )

    torch.onnx.export(
        model,
        (dummy["input_ids"], dummy["attention_mask"]),
        output_path,
        input_names=["input_ids", "attention_mask"],
        output_names=["logits"],
        dynamic_axes={
            "input_ids":      {0: "batch", 1: "seq"},
            "attention_mask": {0: "batch", 1: "seq"},
            "logits":         {0: "batch"},
        },
        opset_version=14,
    )

    print(f"Model exported → {output_path}")
    return accuracy


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="MailDefender model retraining")
    parser.add_argument("--db",           required=True,   help="Path to maildefender.db")
    parser.add_argument("--dataset",      required=True,   help="Path to original dataset.csv")
    parser.add_argument("--checkpoint",   default="ml/model/tokenizer", help="HuggingFace checkpoint dir (tokenizer + weights)")
    parser.add_argument("--output",       default="ml/model/maildefender_new.onnx", help="Output ONNX path")
    parser.add_argument("--min-feedback", type=int, default=50, help="Minimum corrected feedback samples required")
    parser.add_argument("--epochs",       type=int, default=3,  help="Fine-tuning epochs")
    parser.add_argument("--auto-swap",    action="store_true",   help="Replace maildefender.onnx if accuracy passes threshold")
    args = parser.parse_args()

    feedback_df = load_feedback(args.db, args.min_feedback)
    if feedback_df is None:
        sys.exit(1)

    original_df = load_original_dataset(args.dataset)
    combined_df = pd.concat([original_df, feedback_df], ignore_index=True).sample(
        frac=1, random_state=42
    )

    accuracy = train_and_export(combined_df, args.checkpoint, args.output, args.epochs)

    if args.auto_swap:
        prod_path   = str(Path(args.output).parent / "maildefender.onnx")
        backup_path = str(Path(args.output).parent / "maildefender_backup.onnx")
        if Path(prod_path).exists():
            shutil.copy2(prod_path, backup_path)
            print(f"Backed up current model → {backup_path}")
        shutil.copy2(args.output, prod_path)
        print(f"Production model swapped (accuracy: {accuracy:.4f})")
        print("\nReload the ML microservice:")
        print("  curl -X POST https://ml.maildefender.xyz/reload")
    else:
        print(f"\nTo deploy:")
        print(f"  cp {args.output} ml/model/maildefender.onnx")
        print(f"  curl -X POST https://ml.maildefender.xyz/reload")


if __name__ == "__main__":
    main()
