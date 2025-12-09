#!/usr/bin/env bash
set -euo pipefail

# Usage:
#   bulk_register_videos.sh -a /path/to/videos   # add/register all .mp4 files
#   bulk_register_videos.sh -d /path/to/videos   # delete/unregister matching videos

if [[ "${1:-}" != "-a" && "${1:-}" != "-d" ]]; then
  echo "Usage: $0 -a|-d <src_root>"
  exit 1
fi

MODE="$1"      # -a or -d
shift || true

# Folder on your host that contains videos (and subfolders)
SRC_ROOT="${1:-/home/taha-kms/masking/dataset}"

# Project root and target folder (adjust if your path is different)
PROJECT_ROOT="/home/taha-kms/masking/AutoLabelAnything/AutoLabelAnything"
TARGET_DIR="$PROJECT_ROOT/autolabel_data/user_videos"

mkdir -p "$TARGET_DIR"

if [[ "$MODE" == "-a" ]]; then
  echo "Mode: ADD"
  echo "Scanning for .mp4 files under: $SRC_ROOT"
  echo "Copying into: $TARGET_DIR"
  echo

  # Find all .mp4 files (case-insensitive), handle spaces safely
  find "$SRC_ROOT" -type f \( -iname '*.mp4' \) -print0 |
    while IFS= read -r -d '' src; do
      base="$(basename "$src")"
      name="${base%.mp4}"

      echo "Processing: $src"
      echo "  -> copying to: $TARGET_DIR/$base"
      cp -f "$src" "$TARGET_DIR/$base"

      # Tell the API about this video
      json_payload=$(cat <<EOF
{
  "video_name": "$name",
  "video_path": "/data/autolabeling_data/user_videos/$base",
  "target_fps": 20
}
EOF
)

      echo "  -> registering via API..."
      curl -sS -X POST http://localhost:8000/videos/add \
        -H "Content-Type: application/json" \
        -d "$json_payload" || echo "    (warning: API call failed)"
      echo
    done

elif [[ "$MODE" == "-d" ]]; then
  echo "Mode: DELETE"
  echo "Scanning for .mp4 files under: $SRC_ROOT"
  echo "Matching by video_name against backend and deleting."
  echo

  # Require jq for safe JSON parsing
  if ! command -v jq >/dev/null 2>&1; then
    echo "Error: jq is required for delete mode (-d) but is not installed."
    echo "       Install jq (e.g. sudo apt install jq) and rerun."
    exit 1
  fi

  # Cache current videos list once
  videos_json="$(curl -sS http://localhost:8000/videos/ || echo '[]')"

  find "$SRC_ROOT" -type f \( -iname '*.mp4' \) -print0 |
    while IFS= read -r -d '' src; do
      base="$(basename "$src")"
      name="${base%.mp4}"

      echo "Processing for delete: $src (video_name='$name')"

      # Find matching video_id(s) by name
      video_ids=$(printf '%s\n' "$videos_json" | jq -r ".[] | select(.video_name==\"$name\") | .video_id" || true)

      if [[ -z "$video_ids" ]]; then
        echo "  -> no matching video found in API, skipping"
      else
        for vid in $video_ids; do
          echo "  -> deleting video id: $vid via API"
          curl -sS -X DELETE "http://localhost:8000/videos/$vid" \
            || echo "    (warning: DELETE /videos/$vid failed)"
        done
      fi

      # Optionally remove the copied file from target dir if it exists
      if [[ -f "$TARGET_DIR/$base" ]]; then
        echo "  -> removing local copy: $TARGET_DIR/$base"
        rm -f "$TARGET_DIR/$base"
      fi

      echo
    done
fi

echo "Done."