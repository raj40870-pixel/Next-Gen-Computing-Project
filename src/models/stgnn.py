"""
Spatio-Temporal Graph Neural Network (ST-GNN) Architecture
Designed for Groundwater Depletion Forecasting fusing InSAR deformation and rainfall.
Incorporates Spatial Graph Convolutions (spatial aquifer connectivity)
and Gated Temporal Convolutions (seasonal recharge lag and depletion dynamics).
"""

import math
import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Tuple


class SpatialGraphConv(nn.Module):
    """
    Spatial Graph Convolution layer based on Kipf & Welling / Chebyshev formulation.
    Computes H' = A_norm @ H @ W + b
    Input shape:  [B, T, N, C_in]
    Output shape: [B, T, N, C_out]
    """
    def __init__(self, in_features: int, out_features: int, bias: bool = True):
        super().__init__()
        self.in_features = in_features
        self.out_features = out_features
        self.weight = nn.Parameter(torch.Tensor(in_features, out_features))
        if bias:
            self.bias = nn.Parameter(torch.Tensor(out_features))
        else:
            self.register_parameter("bias", None)
        self.reset_parameters()

    def reset_parameters(self):
        nn.init.kaiming_uniform_(self.weight, a=math.sqrt(5))
        if self.bias is not None:
            fan_in, _ = nn.init._calculate_fan_in_and_fan_out(self.weight)
            bound = 1 / math.sqrt(fan_in) if fan_in > 0 else 0
            nn.init.uniform_(self.bias, -bound, bound)

    def forward(self, x: torch.Tensor, adj: torch.Tensor) -> torch.Tensor:
        """
        x:   [B, T, N, C_in]
        adj: [N, N] normalized adjacency matrix
        """
        B, T, N, C = x.shape
        # Linear projection: [B, T, N, C_in] @ [C_in, C_out] -> [B, T, N, C_out]
        support = torch.matmul(x, self.weight)
        
        # Graph convolution: A @ support across node dimension N
        # We can permute to [B, T, C_out, N] or use einsum
        # einsum: 'nm, btmf -> btnf'
        out = torch.einsum("nm,btmf->btnf", adj, support)
        
        if self.bias is not None:
            out = out + self.bias
        return out


class TemporalGatedConv(nn.Module):
    """
    Temporal Gated Convolutional Layer (GLU style)
    Applies 1D causal / dilated convolution along the time axis.
    Input shape:  [B, T, N, C_in]
    Output shape: [B, T', N, C_out]
    """
    def __init__(self, in_channels: int, out_channels: int, kernel_size: int = 3):
        super().__init__()
        self.kernel_size = kernel_size
        self.conv = nn.Conv2d(
            in_channels=in_channels,
            out_channels=2 * out_channels,  # split into filter and gate
            kernel_size=(kernel_size, 1),
            padding=(kernel_size - 1, 0)  # causal padding
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        x: [B, T, N, C]
        Convert to [B, C, T, N] for 2D convolution
        """
        B, T, N, C = x.shape
        x_perm = x.permute(0, 3, 1, 2)  # [B, C, T, N]
        conv_out = self.conv(x_perm)     # [B, 2*C_out, T + K - 1, N]
        # Slice causal padding to keep length T
        conv_out = conv_out[:, :, :T, :]
        
        # Gated Linear Unit (GLU): P * sigmoid(Q)
        P, Q = torch.chunk(conv_out, 2, dim=1)
        out = P * torch.sigmoid(Q)
        
        return out.permute(0, 2, 3, 1)  # [B, T, N, C_out]


class SpatioTemporalBlock(nn.Module):
    """
    ST-Conv Block combining Temporal Gated Conv -> Spatial Graph Conv -> Temporal Gated Conv
    with residual connection and LayerNorm.
    """
    def __init__(self, in_channels: int, hidden_channels: int, out_channels: int, kernel_size: int = 3, dropout: float = 0.15):
        super().__init__()
        self.temporal_conv1 = TemporalGatedConv(in_channels, hidden_channels, kernel_size)
        self.spatial_conv = SpatialGraphConv(hidden_channels, hidden_channels)
        self.temporal_conv2 = TemporalGatedConv(hidden_channels, out_channels, kernel_size)
        
        self.norm = nn.LayerNorm(out_channels)
        self.dropout = nn.Dropout(dropout)
        
        # Residual projection if channel dimensions differ
        if in_channels != out_channels:
            self.residual = nn.Linear(in_channels, out_channels)
        else:
            self.residual = nn.Identity()

    def forward(self, x: torch.Tensor, adj: torch.Tensor) -> torch.Tensor:
        """
        x:   [B, T, N, C_in]
        adj: [N, N]
        """
        res = self.residual(x)
        
        # Temporal Gated Conv 1
        h = self.temporal_conv1(x)
        h = F.relu(h)
        
        # Spatial Graph Conv
        h = self.spatial_conv(h, adj)
        h = F.relu(h)
        h = self.dropout(h)
        
        # Temporal Gated Conv 2
        h = self.temporal_conv2(h)
        
        # Residual and LayerNorm
        h = self.norm(h + res)
        return h


class SpatioTemporalGNN(nn.Module):
    """
    End-to-End Spatio-Temporal Graph Neural Network for Groundwater Forecasting.
    
    Inputs:
      x: [B, T_in, N, num_features] (e.g. InSAR subsidence, rainfall, water depth, ET)
      adj: [N, N] normalized spatial hydrogeological adjacency matrix
    Outputs:
      y_pred: [B, T_out, N] predicted groundwater depth (mbgl) over 30 days
    """
    def __init__(
        self,
        num_nodes: int = 15,
        num_features: int = 4,
        seq_len_in: int = 30,
        seq_len_out: int = 30,
        hidden_dim: int = 64,
        num_blocks: int = 2,
        kernel_size: int = 3,
        dropout: float = 0.15
    ):
        super().__init__()
        self.num_nodes = num_nodes
        self.num_features = num_features
        self.seq_len_in = seq_len_in
        self.seq_len_out = seq_len_out

        # Input feature embedding
        self.feature_embed = nn.Linear(num_features, hidden_dim)

        # Stacked Spatio-Temporal Blocks
        self.blocks = nn.ModuleList([
            SpatioTemporalBlock(
                in_channels=hidden_dim,
                hidden_channels=hidden_dim,
                out_channels=hidden_dim,
                kernel_size=kernel_size,
                dropout=dropout
            )
            for _ in range(num_blocks)
        ])

        # Temporal pooling / transformation from seq_len_in to seq_len_out
        self.temporal_pool = nn.Conv1d(
            in_channels=seq_len_in,
            out_channels=seq_len_out,
            kernel_size=1
        )

        # Node-wise regression head predicting water depth
        self.regressor = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim // 2, 1)
        )

    def forward(self, x: torch.Tensor, adj: torch.Tensor) -> torch.Tensor:
        """
        x:   [B, T_in, N, F]
        adj: [N, N]
        return: [B, T_out, N]
        """
        B, T, N, F = x.shape
        
        # 1. Feature embedding: [B, T, N, F] -> [B, T, N, hidden_dim]
        h = self.feature_embed(x)
        
        # 2. Pass through Spatio-Temporal Blocks
        for block in self.blocks:
            h = block(h, adj)  # [B, T_in, N, hidden_dim]
            
        # 3. Temporal transition: [B, T_in, N, H] -> reshape to [B*N, T_in, H]
        h = h.permute(0, 2, 1, 3).contiguous().view(B * N, self.seq_len_in, -1)
        # Conv1d across time dimension: [B*N, T_out, H]
        h = self.temporal_pool(h)
        h = h.view(B, N, self.seq_len_out, -1).permute(0, 2, 1, 3).contiguous()  # [B, T_out, N, H]
        
        # 4. Final regression head: [B, T_out, N, 1] -> squeeze to [B, T_out, N]
        out = self.regressor(h).squeeze(-1)
        return out


if __name__ == "__main__":
    print("Testing SpatioTemporalGNN architecture...")
    B, T_in, N, F, T_out = 4, 30, 15, 4, 30
    dummy_x = torch.randn(B, T_in, N, F)
    dummy_adj = torch.eye(N)
    
    model = SpatioTemporalGNN(num_nodes=N, num_features=F, seq_len_in=T_in, seq_len_out=T_out)
    pred = model(dummy_x, dummy_adj)
    print(f"Input shape: {dummy_x.shape}")
    print(f"Output shape: {pred.shape}")
    print(f"Total trainable parameters: {sum(p.numel() for p in model.parameters() if p.requires_grad):,}")
    assert pred.shape == (B, T_out, N), "Output shape mismatch!"
    print("Architecture verified successfully!")
