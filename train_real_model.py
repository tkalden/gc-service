#!/usr/bin/env python3
"""
Train the real clothing classifier model with your data
"""

import logging
import os
import sys

import numpy as np
import tensorflow as tf
from tensorflow.keras.applications import Xception
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau
from tensorflow.keras.layers import Dense, Dropout, GlobalAveragePooling2D
from tensorflow.keras.models import Model
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.preprocessing.image import ImageDataGenerator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_model(num_classes=10):
    """Create Xception-based model for clothing classification"""
    base_model = Xception(weights='imagenet', include_top=False, input_shape=(299, 299, 3))
    
    # Freeze base model layers initially
    base_model.trainable = False
    
    # Add custom layers
    x = base_model.output
    x = GlobalAveragePooling2D()(x)
    x = Dense(512, activation='relu')(x)
    x = Dropout(0.3)(x)
    predictions = Dense(num_classes, activation='softmax')(x)
    
    model = Model(inputs=base_model.input, outputs=predictions)
    
    return model, base_model

def train_model():
    """Train the clothing classifier with real data"""
    logger.info("🚀 Starting real clothing classifier training...")
    
    # Data paths
    data_dir = "/Users/tenzinkalden/projects/mlAlgoComparison/src/data/clothes_images"
    
    if not os.path.exists(data_dir):
        logger.error(f"❌ Training data not found at {data_dir}")
        return False
    
    # Check data structure
    train_dir = os.path.join(data_dir, "train")
    val_dir = os.path.join(data_dir, "validation")
    
    if not os.path.exists(train_dir) or not os.path.exists(val_dir):
        logger.error("❌ Train or validation directories not found")
        return False
    
    # Count images
    train_count = sum([len(files) for r, d, files in os.walk(train_dir)])
    val_count = sum([len(files) for r, d, files in os.walk(val_dir)])
    
    logger.info(f"📊 Found {train_count} training images, {val_count} validation images")
    
    # Create model
    model, base_model = create_model()
    
    # Compile model
    model.compile(
        optimizer=Adam(learning_rate=0.001),
        loss='categorical_crossentropy',
        metrics=['accuracy']
    )
    
    logger.info("✅ Model created and compiled")
    
    # Data generators
    train_datagen = ImageDataGenerator(
        rescale=1./255,
        rotation_range=20,
        width_shift_range=0.2,
        height_shift_range=0.2,
        horizontal_flip=True,
        shear_range=0.2,
        zoom_range=0.2,
        fill_mode='nearest'
    )
    
    val_datagen = ImageDataGenerator(rescale=1./255)
    
    # Create generators
    train_generator = train_datagen.flow_from_directory(
        train_dir,
        target_size=(299, 299),
        batch_size=32,
        class_mode='categorical',
        shuffle=True
    )
    
    val_generator = val_datagen.flow_from_directory(
        val_dir,
        target_size=(299, 299),
        batch_size=32,
        class_mode='categorical',
        shuffle=False
    )
    
    logger.info(f"📁 Found {train_generator.num_classes} classes")
    logger.info(f"📁 Class indices: {train_generator.class_indices}")
    
    # Callbacks
    early_stopping = EarlyStopping(
        monitor='val_accuracy',
        patience=5,
        restore_best_weights=True
    )
    
    reduce_lr = ReduceLROnPlateau(
        monitor='val_loss',
        factor=0.2,
        patience=3,
        min_lr=0.0001
    )
    
    # Train model
    logger.info("🎯 Starting training...")
    history = model.fit(
        train_generator,
        epochs=20,
        validation_data=val_generator,
        callbacks=[early_stopping, reduce_lr],
        verbose=1
    )
    
    # Fine-tuning: Unfreeze some layers
    logger.info("🔧 Fine-tuning with unfrozen layers...")
    base_model.trainable = True
    
    # Freeze layers except the last few
    for layer in base_model.layers[:-10]:
        layer.trainable = False
    
    model.compile(
        optimizer=Adam(learning_rate=0.0001),
        loss='categorical_crossentropy',
        metrics=['accuracy']
    )
    
    # Continue training
    history_fine = model.fit(
        train_generator,
        epochs=10,
        validation_data=val_generator,
        callbacks=[early_stopping, reduce_lr],
        verbose=1
    )
    
    # Save model
    model_path = "/Users/tenzinkalden/gc-service/models/clothes_classifier_model.h5"
    model.save(model_path)
    
    logger.info(f"✅ Real model saved to {model_path}")
    logger.info("🎉 Training completed successfully!")
    
    # Print final accuracy
    final_val_acc = max(history.history['val_accuracy'] + history_fine.history['val_accuracy'])
    logger.info(f"📈 Final validation accuracy: {final_val_acc:.2%}")
    
    return True

if __name__ == "__main__":
    try:
        success = train_model()
        if success:
            print("\n🎉 Real model training completed!")
            print("Your smart upload will now use the trained model with real clothing detection.")
        else:
            print("\n❌ Training failed.")
            sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)

