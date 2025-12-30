import pandas as pd
from sklearn.model_selection import train_test_split

from backend.config import DATASET_PATH

def load_dataset() -> pd.DataFrame:
    df = pd.read_csv(DATASET_PATH)
    if "difficulty" not in df.columns:
        df["difficulty"] = "unknown"
    return df

def make_splits(test_size: float = 0.2, val_size: float = 0.1, random_state: int = 42):
    df = load_dataset()
    train_val, test = train_test_split(
        df,
        test_size=test_size,
        stratify=df["difficulty"],
        random_state=random_state,
    )
    relative_val_size = val_size / (1 - test_size)
    train, val = train_test_split(
        train_val,
        test_size=relative_val_size,
        stratify=train_val["difficulty"],
        random_state=random_state,
    )
    return train.reset_index(drop=True), val.reset_index(drop=True), test.reset_index(drop=True)
