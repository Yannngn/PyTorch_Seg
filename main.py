import wandb
import os
import torch
import torch.nn as nn
import torch.optim as optim

import albumentations as A
from albumentations.pytorch import ToTensorV2

from datetime import datetime

from munch import munchify, unmunchify
from yaml import safe_load

from model import UNET
from early_stopping import EarlyStopping
from utils import load_checkpoint, get_loaders, save_validation_as_imgs, get_weights
from train import train_loop

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
PARENT_DIR = os.path.abspath(__file__)
BEGIN = datetime.now().strftime("%Y%m%d_%H%M%S")

with open('config.yaml') as f:
    CONFIG = munchify(safe_load(f))

def main():
    wandb.init(
        project = CONFIG.PROJECT.PROJECT_NAME,
        entity = CONFIG.PROJECT.PROJECT_TEAM,
        config = unmunchify(CONFIG.HYPERPARAMETERS))

    config = wandb.config

    train_transforms, val_transforms = A.Compose([ToTensorV2(),],), A.Compose([ToTensorV2(),],)

    train_loader, val_loader = get_loaders(
        CONFIG.PATHS.TRAIN_IMG_DIR,
        CONFIG.PATHS.TRAIN_MASK_DIR,
        CONFIG.PATHS.VAL_IMG_DIR,
        CONFIG.PATHS.VAL_MASK_DIR,
        CONFIG.HYPERPARAMETERS.BATCH_SIZE,
        train_transforms,
        val_transforms,
        CONFIG.PROJECT.NUM_WORKERS,
        CONFIG.PROJECT.PIN_MEMORY,
    )

    model = UNET(in_channels = CONFIG.IMAGE.IMAGE_CHANNELS, classes = CONFIG.IMAGE.MASK_LABELS, config = config).to(DEVICE)
    model = nn.DataParallel(model)

    if CONFIG.HYPERPARAMETERS.WEIGHTS:
        weights = get_weights(CONFIG.PATHS.TRAIN_MASK_DIR, CONFIG.IMAGE.MASK_LABELS, DEVICE)
        loss_fn = nn.CrossEntropyLoss(weight = weights)
    else:
        loss_fn = nn.CrossEntropyLoss()
    
    if config.optimizer == 'adam':
        optimizer = optim.Adam(model.parameters(), lr=CONFIG.HYPERPARAMETERS.LEARNING_RATE)
    elif config.optimizer == 'sgd':
        optimizer = optim.SGD(model.parameters(), lr=CONFIG.HYPERPARAMETERS.LEARNING_RATE, momentum=0.9, nesterov=True, weight_decay=0.0001)
    else:
        raise KeyError(f"optimizer {config.optimizer} not recognized.")
    
    if CONFIG.PROJECT.SCHEDULER:
        scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, 'min')
    
    load_epoch = 0
    if CONFIG.PROJECT.LOAD_MODEL:
        load_epoch = load_checkpoint(torch.load("my_checkpoint.pth.tar"), model, optimizer, scheduler)

    #check_accuracy(val_loader, model, DEVICE)
    save_validation_as_imgs(val_loader, folder = CONFIG.PATHS.PREDICTIONS_DIR, time = BEGIN, device = DEVICE)

    scaler = torch.cuda.amp.GradScaler()

    stopping = EarlyStopping()

    train_loop(
        train_loader, 
        val_loader, 
        model, 
        optimizer, 
        scheduler, 
        loss_fn, 
        scaler, 
        stopping,
        config,
        load_epoch
    )

if __name__ == "__main__":
    main()