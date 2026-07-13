#!/bin/bash

echo "$(date) check_log.sh 执行" >> /home/azureuser/userEmail/check_log_run.log

cd /home/azureuser/userEmail/

# tokyo_query 日志与容器
CONTAINER1="tokyo_query"
ID1=$(docker inspect --format='{{.Id}}' $CONTAINER1)
LOG1="/var/lib/docker/containers/$ID1/$ID1-json.log"

# user_email1 日志与容器
# CONTAINER2="user_email1"
# ID2=$(docker inspect --format='{{.Id}}' $CONTAINER2)
# LOG2="/var/lib/docker/containers/$ID2/$ID2-json.log"

# 检查 tokyo_query 日志
if [ $(find "$LOG1" -mmin +5 | wc -l) -gt 0 ]; then
  echo "$(date) 重启容器 $CONTAINER1" >> /home/azureuser/userEmail/check_log_run.log
  docker restart $CONTAINER1
fi

# 检查 user_email1 日志
# if [ $(find "$LOG2" -mmin +5 | wc -l) -gt 0 ]; then
#   echo "$(date) 重启容器 $CONTAINER2" >> /home/azureuser/userEmail/check_log_run.log
#   docker restart $CONTAINER2
# fi