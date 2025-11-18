import json
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
from xgboost import XGBClassifier
from sklearn.pipeline import Pipeline
from sklearn.metrics import accuracy_score, classification_report
import joblib
import os

DATA_PATH = "backend/dataset/style_dataset.json"

MODEL_PATH = "backend/models/style_model.pkl"
ENCODER_PATH = "backend/models/style_label_encoder.pkl"


def load_dataset():
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    X = np.array([item["feature"] for item in data])
    y = np.array([item["label"] for item in data])

    return X, y


def train():
    print("📂 加载风格数据集...")
    X, y = load_dataset()
    print("样本数量:", len(X))
    print("特征维度:", X.shape[1])

    # 关键：标签编码（字符串 → 整数）
    encoder = LabelEncoder()
    y_encoded = encoder.fit_transform(y)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y_encoded,
        test_size=0.2,
        random_state=42,
        stratify=y_encoded
    )

    print("🔧 开始训练风格模型（XGBoost）...")

    model = Pipeline([
        ("scaler", StandardScaler()),
        ("clf", XGBClassifier(
            n_estimators=300,
            max_depth=8,
            learning_rate=0.05,
            subsample=0.8,
            colsample_bytree=0.8,
            objective="multi:softmax",
            n_jobs=-1
        ))
    ])

    model.fit(X_train, y_train)

    # 预测
    y_pred = model.predict(X_test)
    acc = accuracy_score(y_test, y_pred)

    print("\n🎯 测试集准确率:", acc)
    print("\n📊 分类报告（数字标签）：")
    print(classification_report(y_test, y_pred))

    # 保存模型与标签编码器
    os.makedirs("backend/models", exist_ok=True)

    joblib.dump(model, MODEL_PATH)
    joblib.dump(encoder, ENCODER_PATH)

    print("\n💾 模型已保存到:", MODEL_PATH)
    print("💾 标签编码器已保存到:", ENCODER_PATH)
    print("标签对应关系:", dict(zip(encoder.classes_, encoder.transform(encoder.classes_))))


if __name__ == "__main__":
    train()
