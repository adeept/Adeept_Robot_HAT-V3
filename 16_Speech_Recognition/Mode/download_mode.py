#!/usr/bin/env python3
# download_sherpa_model.py
# Auto download & extract sherpa-onnx zh-en streaming model
# Skip if model folder already exists, wget with resume support (-c)

import os
import subprocess

def run_command(cmd=""):
    p = subprocess.Popen(
        cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
    )
    result = p.stdout.read().decode("utf-8")
    status = p.poll()
    return status, result

def main():
    url = "https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/sherpa-onnx-streaming-zipformer-bilingual-zh-en-2023-02-20.tar.bz2"
    tar_name = "sherpa-onnx-streaming-zipformer-bilingual-zh-en-2023-02-20.tar.bz2"
    folder_name = "sherpa-onnx-streaming-zipformer-bilingual-zh-en-2023-02-20"

    if os.path.isdir(folder_name):
        print(f"[INFO] Model directory [{folder_name}] already exists, skip download.")
        return

    print(f"[INFO] Start downloading model (resume enabled):\n{url}")
    ret, out = run_command(f"sudo wget -c {url}")
    print(out)
    if ret != 0:
        print("[ERROR] wget download failed!")
        return

    print("\n[INFO] Start extracting archive ...")
    ret, out = run_command(f"sudo tar xvf {tar_name}")
    print(out)
    if ret != 0:
        print("[ERROR] tar extract failed!")
        return

    print("\n✅ Model download and extract completed successfully!")

if __name__ == "__main__":
    main()
