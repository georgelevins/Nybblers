import os
from huggingface_hub import snapshot_download

snapshot_download(
    repo_id="BAAI/bge-base-en-v1.5",
    local_dir="./bge-base-en-v1.5",
    local_dir_use_symlinks=False,
    token=os.environ.get("HF_TOKEN")
)

print("Download complete")