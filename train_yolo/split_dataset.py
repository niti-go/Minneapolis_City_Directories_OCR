import os
import shutil
import random
from pathlib import Path

#I used this script to split the annotated dataset into train and val sets
#In annotated_training_data/images and annotated_training_data/labels, there are now 2 folders: train and val

#To run: % python train_yolo/split_dataset.py

def split_yolo_dataset(export_path, train_ratio=0.8, random_seed=42):
    """
    Split YOLO dataset into train and validation sets
    
    Args:
        export_path: Path to the export folder
        train_ratio: Ratio of training data (default 0.8 = 80%)
        random_seed: Random seed for reproducibility
    """
    
    # Set random seed for reproducibility
    random.seed(random_seed)
    
    # Paths
    images_path = Path(export_path) / "images"
    labels_path = Path(export_path) / "labels"
    
    # Create train and val directories
    train_images = Path(export_path) / "images" / "train"
    train_labels = Path(export_path) / "labels" / "train"
    val_images = Path(export_path) / "images" / "val"
    val_labels = Path(export_path) / "labels" / "val"
    
    # Create directories
    for dir_path in [train_images, train_labels, val_images, val_labels]:
        dir_path.mkdir(parents=True, exist_ok=True)
    
    # Get all image files
    image_files = [f for f in images_path.iterdir() if f.is_file() and f.suffix.lower() in ['.jpg', '.jpeg', '.png']]
    
    # Shuffle and split
    random.shuffle(image_files)
    split_idx = int(len(image_files) * train_ratio)
    train_files = image_files[:split_idx]
    val_files = image_files[split_idx:]
    
    print(f"Total images: {len(image_files)}")
    print(f"Training images: {len(train_files)} ({len(train_files)/len(image_files)*100:.1f}%)")
    print(f"Validation images: {len(val_files)} ({len(val_files)/len(image_files)*100:.1f}%)")
    
    # Move files to train and val directories
    def move_files(file_list, dest_images, dest_labels):
        for img_file in file_list:
            # Move image
            shutil.copy2(img_file, dest_images / img_file.name)
            
            # Move corresponding label
            label_file = labels_path / f"{img_file.stem}.txt"
            if label_file.exists():
                shutil.copy2(label_file, dest_labels / label_file.name)
            else:
                print(f"Warning: No label file found for {img_file.name}")
    
    # Move training files
    print("\nMoving training files...")
    move_files(train_files, train_images, train_labels)
    
    # Move validation files
    print("Moving validation files...")
    move_files(val_files, val_images, val_labels)
    
    print(f"\n✅ Dataset split complete!")
    print(f"Training: {len(list(train_images.iterdir()))} images, {len(list(train_labels.iterdir()))} labels")
    print(f"Validation: {len(list(val_images.iterdir()))} images, {len(list(val_labels.iterdir()))} labels")

# Run the split
if __name__ == "__main__":
    export_path = "train_yolo/annotated_training_data"  # Adjust this path if needed
    split_yolo_dataset(export_path, train_ratio=0.8)