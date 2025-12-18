import os
import json
import joblib
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from xgboost import XGBClassifier
from sklearn.metrics import classification_report

# === 路径 ===
DATA_PATH = "backend/dataset/emomusic_embedding/emotion_dataset.json"
MODEL_PATH = "backend/models/emotion_model.pkl"
LABEL_PATH = "backend/models/emotion_label_encoder.pkl"


def load_dataset():
    print("📂 读取 embedding 数据集...")
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    X = np.array([d["embedding"] for d in data], dtype=np.float32)
    y = np.array([d["label"] for d in data])
    return X, y


def train():
    X, y = load_dataset()
    print(f"数据量：{len(X)}")

    # 标签编码
    le = LabelEncoder()
    y_encoded = le.fit_transform(y)

    # 保存 label encoder
    os.makedirs("backend/models", exist_ok=True)
    joblib.dump(le, LABEL_PATH)

    # 训练模型
    print("🚀 开始训练 XGBoost 情绪模型 ...")
    model = Pipeline([
        ("scaler", StandardScaler()),
        ("clf", XGBClassifier(
            n_estimators=250,
            max_depth=8,
            learning_rate=0.05,
            subsample=0.8,
            colsample_bytree=0.9,
            eval_metric="mlogloss"
        ))
    ])

    X_train, X_test, y_train, y_test = train_test_split(
        X, y_encoded, test_size=0.2, random_state=42, stratify=y_encoded
    )

    model.fit(X_train, y_train)

    # 测试结果
    y_pred = model.predict(X_test)
    print("\n📊 分类结果：")
    print(classification_report(y_test, y_pred, target_names=le.classes_))

    # 保存模型
    joblib.dump(model, MODEL_PATH)
    print(f"\n🎉 模型已保存：{MODEL_PATH}")


if __name__ == "__main__":
    train()
