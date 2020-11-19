docker stop nvr_gcalendar_ruz
docker rm nvr_gcalendar_ruz
docker build -t nvr_gcalendar_ruz .
docker run -d \
 -it \
 --name nvr_gcalendar_ruz \
 --net=host \
 --env-file ../.env_nvr \
 -v $HOME/creds:/gcalendar_ruz/creds \
 nvr_gcalendar_ruz
