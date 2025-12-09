import argparse
from pathlib import Path

import cv2 as cv
import h5py
import numpy as np


def h5_to_mp4(
    h5_path: Path,
    mp4_path: Path,
    dataset_name: str = "frames",
    fps: int = 20,
) -> None:
    """
    Read a binary-mask video from an H5 file and write it as an MP4.

    The H5 file is expected to have a dataset named `frames` with shape:
        (T, H, W) or (T, H, W, 3), dtype uint8.
    """
    if not h5_path.is_file():
        raise FileNotFoundError(f"H5 file not found: {h5_path}")

    with h5py.File(h5_path, "r") as f:
        if dataset_name not in f:
            raise KeyError(f"Dataset '{dataset_name}' not found in {h5_path}")
        data = f[dataset_name][:]

    if data.ndim == 3:
        # (T, H, W) -> (T, H, W, 3) grayscale -> BGR
        data = np.stack([data] * 3, axis=-1)
    elif data.ndim == 4 and data.shape[-1] == 1:
        # (T, H, W, 1) -> (T, H, W, 3)
        data = np.repeat(data, 3, axis=-1)
    elif data.ndim != 4 or data.shape[-1] not in (1, 3):
        raise ValueError(
            f"Unsupported data shape {data.shape}; expected (T,H,W) or (T,H,W,1/3)"
        )

    data = data.astype(np.uint8)

    t, h, w, c = data.shape
    if c != 3:
        raise ValueError(f"Expected 3-channel frames after conversion, got c={c}")

    mp4_path.parent.mkdir(parents=True, exist_ok=True)

    fourcc = cv.VideoWriter_fourcc(*"mp4v")
    writer = cv.VideoWriter(str(mp4_path), fourcc, float(fps), (w, h), True)
    if not writer.isOpened():
        raise RuntimeError(f"Could not open VideoWriter for {mp4_path}")

    try:
        for i in range(t):
            frame = data[i]
            # Ensure shape is (H, W, 3)
            if frame.shape != (h, w, 3):
                frame = cv.resize(frame, (w, h))
            writer.write(frame)
    finally:
        writer.release()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Convert an H5 'frames' dataset into an MP4 video."
    )
    parser.add_argument(
        "h5_path",
        type=str,
        help="Path to input H5 file (e.g. autolabeling_data/h5/<video>.h5)",
    )
    parser.add_argument(
        "mp4_path",
        type=str,
        nargs="?",
        help="Output MP4 path (default: same as H5, with .mp4 extension)",
    )
    parser.add_argument(
        "--dataset",
        type=str,
        default="frames",
        help="Dataset name inside H5 (default: frames)",
    )
    parser.add_argument(
        "--fps",
        type=int,
        default=20,
        help="Frames per second for output video (default: 20)",
    )

    args = parser.parse_args()

    h5_path = Path(args.h5_path)
    if args.mp4_path:
        mp4_path = Path(args.mp4_path)
    else:
        mp4_path = h5_path.with_suffix(".mp4")

    h5_to_mp4(h5_path, mp4_path, dataset_name=args.dataset, fps=args.fps)
    print(f"Wrote MP4 to: {mp4_path}")


if __name__ == "__main__":
    main()




