#!/usr/bin/env python
"""
make_mesh.py
============

End-to-end driver script for:

  1.  Multi-view image synthesis with **Wonder3D**
  2.  3-D reconstruction + texturing with **DreamGaussian**
  3.  Optional mesh clean-up & GLB export

Run inside the Docker image you built (CUDA runtime present) :

    python make_mesh.py \
        --input /in/photo.jpg \
        --output /out/model.glb \
        --w3d_ckpt /weights/wonder3d.ckpt \
        --dg_ckpt /weights/dreamgaussian.ckpt
"""

import argparse
import os
import shutil
import subprocess
import tempfile
from pathlib import Path


def sh(cmd: str, cwd: str | Path | None = None):
    """Run a shell command and stream its output."""
    print(f"Running: {cmd}")
    subprocess.check_call(cmd, shell=True, cwd=cwd)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, help="Path to input image")
    ap.add_argument("--output", required=True, help="Path to output .glb")
    ap.add_argument("--w3d_ckpt", required=True, help="Wonder3D checkpoint (.ckpt)")
    ap.add_argument("--dg_ckpt", required=True, help="DreamGaussian checkpoint (.ckpt)")
    ap.add_argument("--views", type=int, default=24)
    ap.add_argument("--res", type=int, default=512)
    ap.add_argument("--dg_iters", type=int, default=8000)
    ap.add_argument("--decimate", type=float, default=0.30)
    args = ap.parse_args()

    # Absolute paths
    args.input = os.path.abspath(args.input)
    args.output = os.path.abspath(args.output)

    with tempfile.TemporaryDirectory() as temp_work:
        work = Path(temp_work)
        mv_dir = work / "multiview"
        dg_out = work / "dg"
        mv_dir.mkdir(parents=True, exist_ok=True)

        # --- 1.  Wonder3D ----------------------------------------------------
        w3d_cmd = (
            "python demo.py "
            f"--input {args.input} "
            f"--out_dir {mv_dir} "
            f"--n_views {args.views} "
            f"--res {args.res} "
            f"--ckpt {args.w3d_ckpt} "
            "--bs 1"
        )
        sh(w3d_cmd, cwd="/app/wonder3d")

        # --- 2.  DreamGaussian ----------------------------------------------
        dg_cmd = (
            "python launch.py "
            f"--img_dir {mv_dir/'rgb'} "
            f"--normal_dir {mv_dir/'normal'} "
            f"--out_dir {dg_out} "
            f"--iters {args.dg_iters} "
            f"--ckpt {args.dg_ckpt}"
        )
        sh(dg_cmd, cwd="/app/dreamgaussian")

        # Path conventions in DreamGaussian
        raw_mesh = dg_out / "mesh_raw.obj"
        tex_img = dg_out / "texture.png"
        clean_mesh = dg_out / "mesh_clean.obj"

        # --- 3.  Mesh clean-up ----------------------------------------------
        sh(
            f"python tools/mesh_clean.py {raw_mesh} "
            f"--decimate {args.decimate} "
            f"--laplacian 10 "
            f"--out {clean_mesh}",
            cwd="/app/dreamgaussian",
        )

        # --- 4.  GLB export --------------------------------------------------
        sh(
            f"python tools/export_glb.py {clean_mesh} {tex_img} {args.output}",
            cwd="/app/dreamgaussian",
        )

        print(f"Success: Saved mesh to {args.output}")


if __name__ == "__main__":
    main()
