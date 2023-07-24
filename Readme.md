docs :http://127.0.0.1:8000/docs



```angular2html
celery -A celery_task_app.worker flower --port=5555 --basic-auth=caopv:1207
```
``` angular2html
celery -A celery_task_app.worker worker  --loglevel=INFO -Q foo
```
```angular2html
sh run_backend.sh
```

sudo sshfs -o allow_other upr@172.16.10.49:/home/upr/upr-app/upr-training-be/uploads  /home/admin1/mnt_raid1/md0/caopv/yolo_api/uploads
sudo sshfs -o allow_other upr@172.16.10.49:/home/upr/upr-app/upr-training-be/uploads  /home/pvc/Project/BE_yolo/uploads/

umount /home/admin1/mnt_raid1/md0/caopv/yolo_api/uploads