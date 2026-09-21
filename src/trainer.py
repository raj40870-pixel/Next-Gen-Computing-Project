"""
Trainer Module for Spatio-Temporal Graph Neural Network (ST-GNN)
Handles training loops, validation monitoring, gradient clipping, and checkpointing.
"""

import os
import time
import numpy as np
import torch
import torch.nn as nn
from typing import Dict, Any, List, Tuple
from .models.stgnn import SpatioTemporalGNN


class STGNNTrainer:
    """Trains the ST-GNN forecasting model with validation early stopping."""
    def __init__(
        self,
        model: SpatioTemporalGNN,
        adj_matrix: torch.Tensor,
        lr: float = 0.002,
        weight_decay: float = 1e-4,
        device: str = "cpu",
        checkpoint_dir: str = "checkpoints"
    ):
        self.device = torch.device(device)
        self.model = model.to(self.device)
        self.adj = adj_matrix.to(self.device)
        self.optimizer = torch.optim.Adam(self.model.parameters(), lr=lr, weight_decay=weight_decay)
        self.scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(self.optimizer, mode="min", factor=0.5, patience=3)
        self.criterion = nn.MSELoss()
        self.checkpoint_dir = checkpoint_dir
        os.makedirs(checkpoint_dir, exist_ok=True)
        self.best_checkpoint_path = os.path.join(checkpoint_dir, "best_stgnn.pt")

    def fit(
        self,
        train_data: Dict[str, np.ndarray],
        val_data: Dict[str, np.ndarray],
        epochs: int = 25,
        batch_size: int = 32,
        patience: int = 6,
        verbose: bool = True
    ) -> Dict[str, List[float]]:
        """
        train_data: dict with "X": [B, T_in, N, F], "Y": [B, T_out, N]
        val_data: dict with "X": [B_val, T_in, N, F], "Y": [B_val, T_out, N]
        """
        train_x = torch.tensor(train_data["X"], dtype=torch.float32)
        train_y = torch.tensor(train_data["Y"], dtype=torch.float32)
        val_x = torch.tensor(val_data["X"], dtype=torch.float32).to(self.device)
        val_y = torch.tensor(val_data["Y"], dtype=torch.float32).to(self.device)

        train_dataset = torch.utils.data.TensorDataset(train_x, train_y)
        train_loader = torch.utils.data.DataLoader(train_dataset, batch_size=batch_size, shuffle=True)

        history = {"train_loss": [], "val_loss": []}
        best_val_loss = float("inf")
        patience_counter = 0

        start_time = time.time()
        if verbose:
            print(f"Starting ST-GNN Training for {epochs} epochs on {self.device}...")

        for epoch in range(1, epochs + 1):
            self.model.train()
            total_train_loss = 0.0

            for batch_x, batch_y in train_loader:
                batch_x, batch_y = batch_x.to(self.device), batch_y.to(self.device)
                self.optimizer.zero_grad()
                
                preds = self.model(batch_x, self.adj)
                loss = self.criterion(preds, batch_y)
                loss.backward()
                nn.utils.clip_grad_norm_(self.model.parameters(), max_norm=5.0)
                self.optimizer.step()
                
                total_train_loss += loss.item() * len(batch_x)

            epoch_train_loss = total_train_loss / len(train_dataset)

            # Validation
            self.model.eval()
            with torch.no_grad():
                val_preds = self.model(val_x, self.adj)
                epoch_val_loss = self.criterion(val_preds, val_y).item()

            self.scheduler.step(epoch_val_loss)
            history["train_loss"].append(epoch_train_loss)
            history["val_loss"].append(epoch_val_loss)

            if verbose and (epoch % 5 == 0 or epoch == 1 or epoch == epochs):
                print(f"Epoch {epoch:02d}/{epochs:02d} | Train MSE: {epoch_train_loss:.4f} | Val MSE: {epoch_val_loss:.4f}")

            # Checkpoint best model
            if epoch_val_loss < best_val_loss:
                best_val_loss = epoch_val_loss
                patience_counter = 0
                torch.save({
                    "epoch": epoch,
                    "model_state_dict": self.model.state_dict(),
                    "optimizer_state_dict": self.optimizer.state_dict(),
                    "val_loss": epoch_val_loss,
                    "history": history
                }, self.best_checkpoint_path)
            else:
                patience_counter += 1
                if patience_counter >= patience:
                    if verbose:
                        print(f"Early stopping triggered at epoch {epoch}. Best Val Loss: {best_val_loss:.4f}")
                    break

        elapsed = time.time() - start_time
        if verbose:
            print(f"Training completed in {elapsed:.1f}s. Best model saved to {self.best_checkpoint_path}")

        # Load best weights
        if os.path.exists(self.best_checkpoint_path):
            ckpt = torch.load(self.best_checkpoint_path, map_location=self.device)
            self.model.load_state_dict(ckpt["model_state_dict"])

        return history

    def predict(self, test_x: np.ndarray, batch_size: int = 64) -> np.ndarray:
        """
        test_x: [B, T_in, N, F]
        returns: [B, T_out, N]
        """
        self.model.eval()
        dataset = torch.utils.data.TensorDataset(torch.tensor(test_x, dtype=torch.float32))
        loader = torch.utils.data.DataLoader(dataset, batch_size=batch_size, shuffle=False)
        all_preds = []

        with torch.no_grad():
            for (bx,) in loader:
                bx = bx.to(self.device)
                pred = self.model(bx, self.adj)
                all_preds.append(pred.cpu().numpy())

        return np.concatenate(all_preds, axis=0)
