BASE_URL="http://localhost:8000"
ROOT="/home/taha-kms/masking/AutoLabelAnything/AutoLabelAnything/autolabeling_data/autolabeling_data/semantic_color_frames"

for d in "$ROOT"/*/; do
  uuid="$(basename "$d")"

  # Get task info -> video_id
  video_id=$(curl -s "${BASE_URL}/tasks/${uuid}" | jq -r '.data.video_id' 2>/dev/null)
  if [ -z "$video_id" ] || [ "$video_id" = "null" ]; then
    echo "$uuid: <no task/video found>"
    continue
  fi

  # Get video info -> video_name
  video_name=$(curl -s "${BASE_URL}/videos/${video_id}" | jq -r '.video_name' 2>/dev/null)
  echo "$uuid: $video_name"
done