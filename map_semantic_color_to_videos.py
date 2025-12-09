#!/usr/bin/env python
import os
import sys

# Paths in your project
API_ROOT = "/home/taha-kms/masking/AutoLabelAnything/AutoLabelAnything/autolabel-anything-api"
SEMANTIC_COLOR_ROOT = (
    "/home/taha-kms/masking/AutoLabelAnything/AutoLabelAnything/"
    "autolabeling_data/autolabeling_data/semantic_color_frames"
)

# Make the API package importable
sys.path.append(API_ROOT)

from db.database import SessionLocal  # type: ignore
import database_models as dbmodels    # type: ignore


def main():
    db = SessionLocal()
    try:
        for folder in sorted(os.listdir(SEMANTIC_COLOR_ROOT)):
            folder_path = os.path.join(SEMANTIC_COLOR_ROOT, folder)
            if not os.path.isdir(folder_path):
                continue

            task_uuid = folder
            task = (
                db.query(dbmodels.Task)
                .filter(dbmodels.Task.task_uuid == task_uuid)
                .first()
            )
            if not task:
                print(f"{task_uuid}: <no Task row found>")
                continue

            video = (
                db.query(dbmodels.Video)
                .filter(dbmodels.Video.video_id == task.video_id)
                .first()
            )
            if not video:
                print(f"{task_uuid}: <no Video row found> (video_id={task.video_id})")
                continue

            print(
                f"{task_uuid}: video_id={video.video_id}, video_name={video.video_name}"
            )
    finally:
        db.close()


if __name__ == "__main__":
    main()