export APP = browser
export APP_PATH := $(shell pwd)
export APP_VERSION	:= 1.0
export DATA_PATH = ${APP_PATH}/backend/tests/iga/data
#export APP_VERSION	:= $(shell git describe --tags || cat VERSION )

# docker compose
export DC := /usr/local/bin/docker-compose
export DC_DIR=${APP_PATH}
export DC_FILE=${DC_DIR}/docker-compose
export DC_PREFIX := $(shell echo ${APP} | tr '[:upper:]' '[:lower:]' | tr '_' '-')
export DC_NETWORK := $(shell echo ${APP} | tr '[:upper:]' '[:lower:]')

# elasticsearch defaut configuration
export ES_HOST = elasticsearch
export ES_PORT = 9200
export ES_TIMEOUT = 60
export ES_INDEX = deces
export ES_DATA = ${APP_PATH}/esdata
export ES_NODES = 1
export ES_MEM = 1024m
export ES_VERSION = 7.6.0

export API_PATH = deces
export ES_PROXY_PATH = /${API_PATH}/api/v0/search

export NPM_REGISTRY = $(shell echo $$NPM_REGISTRY )
export NPM_VERBOSE = 1

# BACKEND dir
export BACKEND=${APP_PATH}/backend
export BACKEND_PORT=5000
export BACKEND_HOST=backend

# frontend dir
export FRONTEND_PORT=3000
export FRONTEND = ${APP_PATH}/frontend
export FRONTEND_DEV_HOST = frontend-development
export FILE_FRONTEND_APP_VERSION = $(APP)-$(APP_VERSION)-frontend.tar.gz
export PDFJS_VERSION=2.3.200
# nginx
export NGINX = ${APP_PATH}/nginx
export NGINX_TIMEOUT = 30
export API_USER_LIMIT_RATE=1r/s
export API_USER_BURST=20 nodelay
export API_USER_SCOPE=http_x_forwarded_for
export API_GLOBAL_LIMIT_RATE=20r/s
export API_GLOBAL_BURST=200 nodelay

# traefik
export TRAEFIK_PATH=${APP_PATH}/traefik
export LOG_LEVEL=DEBUG

# this is usefull with most python apps in dev mode because if stdout is
# buffered logs do not shows in realtime
PYTHONUNBUFFERED=1

dummy		    := $(shell touch artifacts)
include ./artifacts
export

#vm_max_count            := $(shell cat /etc/sysctl.conf | egrep vm.max_map_count\s*=\s*262144 && echo true)
#
#vm_max:
#ifeq ("$(vm_max_count)", "")
#	@echo updating vm.max_map_count $(vm_max_count) to 262144
#	sudo sysctl -w vm.max_map_count=262144
#endif

#############
#  Network  #
#############

network-stop:
	docker network rm ${DC_NETWORK}

network:
	@docker network create ${DC_NETWORK_OPT} ${DC_NETWORK} 2> /dev/null; true


# Elasticsearch

elasticsearch: network
	# vm_max
	@echo docker-compose up elasticsearch with ${ES_NODES} nodes
	@cat ${DC_FILE}-elasticsearch.yml | sed "s/%M/${ES_MEM}/g" > ${DC_FILE}-elasticsearch-huge.yml
	@(if [ ! -d ${ES_DATA}/node1 ]; then sudo mkdir -p ${ES_DATA}/node1 ; sudo chmod g+rwx ${ES_DATA}/node1; sudo chgrp 0 ${ES_DATA}/node1; fi)
	@(i=$(ES_NODES); while [ $${i} -gt 1 ]; \
		do \
			if [ ! -d ${ES_DATA}/node$$i ]; then (echo ${ES_DATA}/node$$i && sudo mkdir -p ${ES_DATA}/node$$i && sudo chmod g+rw ${ES_DATA}/node$$i/. && sudo chgrp 1000 ${ES_DATA}/node$$i/.); fi; \
		cat ${DC_FILE}-elasticsearch-node.yml | sed "s/%N/$$i/g;s/%MM/${ES_MEM}/g;s/%M/${ES_MEM}/g" >> ${DC_FILE}-elasticsearch-huge.yml; \
		i=`expr $$i - 1`; \
	done;\
	true)
	${DC} -f ${DC_FILE}-elasticsearch-huge.yml up --build -d

elasticsearch-stop:
	@echo docker-compose down elasticsearch
	@if [ -f "${DC_FILE}-elasticsearch-huge.yml" ]; then ${DC} -f ${DC_FILE}-elasticsearch-huge.yml down;fi

elasticsearch-exec:
		$(DC) -f ${DC_FILE}-elasticsearch.yml exec elasticsearch bash
# kibana

kibana: network
	${DC} -f ${DC_FILE}-kibana.yml up -d

kibana-exec:
	$(DC) -f ${DC_FILE}-kibana.yml exec kibana bash
# traefik

traefik/acme.json:
	touch traefik/acme.json

# backend

# development mode
backend/.env:
	cp backend/.env.sample backend/.env

backend-dev: backend/.env
	@echo docker-compose up backend for dev
	#@export ${DC} -f ${DC_FILE}.yml up -d --build --force-recreate 2>&1 | grep -v orphan
	@export EXEC_ENV=dev;${DC} -f ${DC_FILE}.yml up -d  #--build --force-recreate


backend-dev-stop:
	@export EXEC_ENV=dev; ${DC} -f ${DC_FILE}.yml down #--remove-orphan

# production mode
backend-start: backend/.env
	@echo docker-compose up backend for production ${VERSION}
	@export EXEC_ENV=prod; ${DC} -f ${DC_FILE}.yml up --build -d 2>&1 | grep -v orphan

backend-stop:
	@echo docker-compose down backend for production ${VERSION}
	@export EXEC_ENV=prod; ${DC} -f ${DC_FILE}.yml down  --remove-orphan

backend-exec:
	$(DC) -f ${DC_FILE}.yml exec backend bash

##############
#Test backend#
##############
download-data:
	git clone https://github.com/victorjourne/IGA-BF.git && cd IGA-BF && make run base_path=$(BACKEND)/tests/iga/data/pdf

test:
	$(DC) -f ${DC_FILE}.yml exec backend pytest tests/


##############
#  NGINX     #
##############

nginx: network
	@export EXEC_ENV=dev; ${DC} -f ${DC_FILE}-nginx.yml up -d --build --force-recreate

##############
#  Frontend  #
##############


frontend-dev:
	@echo docker-compose run ${APP} frontend
	@echo ${DATA_PATH}

	@export EXEC_ENV=dev; ${DC} -f ${DC_FILE}-frontend.yml up -d --build --force-recreate

frontend-exec:
	$(DC) -f ${DC_FILE}-frontend.yml exec frontend sh



frontend-dev-stop:
	@export EXEC_ENV=dev; ${DC} -f ${DC_FILE}-frontend.yml down

frontend-stop:
	@export EXEC_ENV=dev; ${DC} -f ${DC_FILE}.yml down

${FRONTEND}/$(FILE_FRONTEND_APP_VERSION):
	( cd ${FRONTEND} && tar -zcvf $(FILE_FRONTEND_APP_VERSION) --exclude ${APP}.tar.gz \
		.eslintrc.js \
		rollup.config.js \
        src \
        public )

frontend-check-build:
	${DC} -f $(DC_FILE)-build.yml config -q

frontend-build-dist: ${FRONTEND}/$(FILE_FRONTEND_APP_VERSION) frontend-check-build
	@echo building ${APP} frontend in ${FRONTEND}
	@export EXEC_ENV=prod; ${DC} -f $(DC_FILE)-build.yml build $(DC_BUILD_ARGS)

dev: network frontend-stop frontend-dev
