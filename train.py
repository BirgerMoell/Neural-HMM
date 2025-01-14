r"""
train.py 

PyTorch-Lightning Trainer file, main file to run your training
"""
import argparse
import os

import pytorch_lightning as pl
from pytorch_lightning.loggers import TensorBoardLogger
from pytorch_lightning.plugins import DDPPlugin
from pytorch_lightning.utilities.seed import seed_everything

from run_tests import run_tests
from src.data_module import LightningLoader
from src.hparams import create_hparams
from src.training_module import TrainingModule

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--checkpoint_path', type=str, default=None,
                        required=False, help='checkpoint path')
    parser.add_argument('-r', '--run-name', type=str, default=None,
                        required=False, help='run name')
    parser.add_argument('-g', '--gpus', nargs='*', default=None,
                        required=False, help='gpu')
    args = parser.parse_args()

    if args.checkpoint_path and not os.path.exists(args.checkpoint_path):
        raise FileExistsError("Check point not present recheck the name")

    hparams = create_hparams()
    if args.run_name:
        hparams.run_name = args.run_name

    if args.gpus:
        hparams.gpus = args.gpus

    if hparams.run_tests:
        run_tests()

    seed_everything(hparams.seed)

    data_module = LightningLoader(hparams)
    model = TrainingModule(hparams)

    logger = TensorBoardLogger(
        hparams.tensorboard_log_dir, name=hparams.run_name)

    trainer = pl.Trainer(resume_from_checkpoint=args.checkpoint_path,
                         gpus=hparams.gpus,
                         logger=logger,
                         log_every_n_steps=1,
                         flush_logs_every_n_steps=1,
                         plugins=DDPPlugin(find_unused_parameters=False) if len(
                             hparams.gpus) > 1 else None,
                         accelerator='ddp' if len(hparams.gpus) > 1 else None,
                         val_check_interval=hparams.val_check_interval,
                         gradient_clip_val=hparams.grad_clip_thresh,
                         track_grad_norm=2,
                         max_epochs=hparams.max_epochs,
                         stochastic_weight_avg=hparams.stochastic_weight_avg,
                         precision=hparams.precision,
                         )

    trainer.fit(model, data_module)
