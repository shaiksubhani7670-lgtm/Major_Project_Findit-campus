"""
FindIt Campus — YOLOv8 Training Script
Fine-tune YOLOv8 for campus-specific lost item detection.
"""

import os
import yaml
import argparse
from pathlib import Path


def create_dataset_config(data_dir, output_path):
    """Create YOLO dataset configuration file."""
    config = {
        'path': str(data_dir),
        'train': 'images/train',
        'val': 'images/val',
        'test': 'images/test',
        'nc': 20,  # Number of classes
        'names': [
            'laptop', 'mobile', 'wallet', 'watch', 'keys',
            'id_card', 'bag', 'bottle', 'books', 'earbuds',
            'headphones', 'calculator', 'power_bank', 'helmet',
            'shoes', 'jewelry', 'usb_drive', 'clothes', 'umbrella', 'other',
        ],
    }

    with open(output_path, 'w') as f:
        yaml.dump(config, f, default_flow_style=False)

    print(f"Dataset config saved to {output_path}")
    return config


def train_yolov8(
    data_yaml,
    model_size='n',
    epochs=100,
    batch_size=16,
    image_size=640,
    output_dir='runs/detect/findit',
    device='cpu',
):
    """
    Fine-tune YOLOv8 on campus lost items dataset.

    Args:
        data_yaml: Path to dataset configuration YAML
        model_size: YOLOv8 model size ('n', 's', 'm', 'l', 'x')
        epochs: Number of training epochs
        batch_size: Training batch size
        image_size: Input image size
        output_dir: Output directory for trained model
        device: Training device ('cpu', '0', '0,1', etc.)
    """
    try:
        from ultralytics import YOLO
    except ImportError:
        print("Error: ultralytics package not found. Install with: pip install ultralytics")
        return

    # Load pre-trained model
    model_name = f'yolov8{model_size}.pt'
    print(f"\n{'='*60}")
    print(f"FindIt Campus — YOLOv8 Training")
    print(f"{'='*60}")
    print(f"Model: {model_name}")
    print(f"Epochs: {epochs}")
    print(f"Batch Size: {batch_size}")
    print(f"Image Size: {image_size}")
    print(f"Device: {device}")
    print(f"Dataset: {data_yaml}")
    print(f"{'='*60}\n")

    model = YOLO(model_name)

    # Train the model
    results = model.train(
        data=data_yaml,
        epochs=epochs,
        batch=batch_size,
        imgsz=image_size,
        project=output_dir,
        name='findit_campus',
        device=device,
        patience=20,
        save=True,
        save_period=10,
        pretrained=True,
        optimizer='Adam',
        lr0=0.001,
        lrf=0.01,
        warmup_epochs=5,
        augment=True,
        hsv_h=0.015,
        hsv_s=0.7,
        hsv_v=0.4,
        degrees=10,
        translate=0.1,
        scale=0.5,
        fliplr=0.5,
        mosaic=1.0,
        verbose=True,
    )

    # Save best model
    best_model_path = os.path.join(output_dir, 'findit_campus', 'weights', 'best.pt')
    final_model_path = os.path.join(os.path.dirname(data_yaml), '..', 'models', 'yolov8_findit.pt')

    if os.path.exists(best_model_path):
        import shutil
        os.makedirs(os.path.dirname(final_model_path), exist_ok=True)
        shutil.copy2(best_model_path, final_model_path)
        print(f"\n✅ Best model saved to: {final_model_path}")

    # Validate
    print("\n📊 Validating model on test set...")
    metrics = model.val(data=data_yaml)
    print(f"mAP50: {metrics.box.map50:.4f}")
    print(f"mAP50-95: {metrics.box.map:.4f}")

    return results


def main():
    parser = argparse.ArgumentParser(description='Train YOLOv8 for FindIt Campus')
    parser.add_argument('--data', type=str, default='ml/datasets/findit.yaml',
                        help='Path to dataset config YAML')
    parser.add_argument('--model', type=str, default='n',
                        choices=['n', 's', 'm', 'l', 'x'],
                        help='YOLOv8 model size')
    parser.add_argument('--epochs', type=int, default=100,
                        help='Number of training epochs')
    parser.add_argument('--batch', type=int, default=16,
                        help='Batch size')
    parser.add_argument('--imgsz', type=int, default=640,
                        help='Input image size')
    parser.add_argument('--device', type=str, default='cpu',
                        help='Device: cpu or gpu id (0, 0,1, etc.)')
    parser.add_argument('--output', type=str, default='runs/detect',
                        help='Output directory')
    parser.add_argument('--create-config', action='store_true',
                        help='Create dataset configuration file')
    parser.add_argument('--data-dir', type=str, default='ml/datasets',
                        help='Dataset directory (for config creation)')

    args = parser.parse_args()

    if args.create_config:
        create_dataset_config(args.data_dir, args.data)
    else:
        train_yolov8(
            data_yaml=args.data,
            model_size=args.model,
            epochs=args.epochs,
            batch_size=args.batch,
            image_size=args.imgsz,
            output_dir=args.output,
            device=args.device,
        )


if __name__ == '__main__':
    main()
