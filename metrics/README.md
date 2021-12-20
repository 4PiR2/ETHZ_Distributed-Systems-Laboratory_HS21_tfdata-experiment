# Prometheus + Grafana

##### Setup

- Install docker-compose: [link](https://docs.docker.com/compose/install/)
- Enable docker to use GPU: [link](https://docs.docker.com/config/containers/resource_constraints/#access-an-nvidia-gpu)
  - A reference for docker compose: [link](https://docs.docker.com/compose/gpu-support/)
- Be able to run docker without sudo: [link](https://docs.docker.com/engine/install/linux-postinstall/#manage-docker-as-a-non-root-user)
- Make sure `chmod -R 777 metrics`

##### Startup

- Nginx and Prometheus
  - `cd` to the nginx and prometheus folder 
  - Start: `docker-compose up -d`
  - Stop: `docker-compose down`
- Prometheus2
  - (Re)Start: `python metrics.py`
  - Stop: `python metrics.py -s`

