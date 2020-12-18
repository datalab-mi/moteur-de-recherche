export APP = moteur-de-recherche
export APP_PATH := $(shell pwd)
export APP_VERSION	:= 0.2
export DATA_PATH = ${APP_PATH}/backend/tests/iga/data
#export APP_VERSION	:= $(shell git describe --tags || cat VERSION )

# docker compose
export DC := /usr/local/bin/docker-compose
export DC_DIR = ${APP_PATH}
export DC_FILE = ${DC_DIR}/docker-compose
export DC_PREFIX := $(shell echo ${APP} | tr '[:upper:]' '[:lower:]' | tr '_' '-')
export DC_NETWORK := $(shell echo ${APP} | tr '[:upper:]' '[:lower:]')
export DC_BUILD_ARGS = --pull --no-cache
export DC_UP_ARGS = --build --force-recreate
export DC_NETWORK_OPT = --opt com.docker.network.driver.mtu=1450

# elasticsearch defaut configuration
export ES_HOST = ${APP}-elasticsearch
export ES_PORT = 9200
export ES_TIMEOUT = 60
export ES_INDEX = test
export ES_DATA = ${APP_PATH}/esdata
export ES_NODES = 1
export ES_MEM = 1024m
export ES_VERSION = 7.6.0

export API_PATH = test
export ES_PROXY_PATH = /${API_PATH}/api/v0/search

export NPM_REGISTRY = $(shell echo $$NPM_REGISTRY )
export NPM_VERBOSE = 1

# KIBANA
export KIBANA_HOST = kibana
export KIBANA_PORT = 5601

# LOGSTASH
export LOGSTASH_HOST = logstash
# BACKEND dir
export BACKEND=${APP_PATH}/backend
export BACKEND_PORT=5000
export BACKEND_HOST = backend

# frontend dir
export FRONTEND_PORT=3000
export FRONTEND = ${APP_PATH}/frontend
export FRONTEND_DEV_HOST = frontend-dev
export FILE_FRONTEND_APP_VERSION = $(APP)-$(APP_VERSION)-frontend.tar.gz
export FILE_FRONTEND_DIST_APP_VERSION = $(APP)-$(APP_VERSION)-frontend-dist.tar.gz
export FILE_FRONTEND_DIST_LATEST_VERSION = $(APP)-latest-frontend-dist.tar.gz

export PDFJS_VERSION=2.3.200
export BUILD_DIR = ${APP_PATH}/${APP}-build
# nginx
export PORT = 80
export NGINX = ${APP_PATH}/nginx
export NGINX_TIMEOUT = 30
export API_USER_LIMIT_RATE=1r/s
export API_USER_BURST=20 nodelay
export API_USER_SCOPE=http_x_forwarded_for
export API_GLOBAL_LIMIT_RATE=20r/s
export API_GLOBAL_BURST=200 nodelay

# this is usefull with most python apps in dev mode because if stdout is
# buffered logs do not shows in realtime
PYTHONUNBUFFERED=1

dummy		    := $(shell touch artifacts)
include ./artifacts
export
# SWIFT
export BUCKET_NAME=${INDEX_NAME}

#vm_max_count            := $(shell cat /etc/sysctl.conf | egrep vm.max_map_count\s*=\s*262144 && echo true)
#
#vm_max:
#ifeq ("$(vm_max_count)", "")
#	@echo updating vm.max_map_count $(vm_max_count) to 262144
#	sudo sysctl -w vm.max_map_count=262144
#endif

#############
#  Network  #npx sapper export
#############

network-stop:
	docker network rm ${DC_NETWORK}

network:
	@docker network create ${DC_NETWORK_OPT} ${DC_NETWORK} 2> /dev/null; true


# Elasticsearchnpx sapper export

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
	${DC} -f ${DC_FILE}-elasticsearch-huge.yml up -d  $(DC_UP_ARGS)

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

kibana-stop:
	${DC} -f ${DC_FILE}-kibana.yml down

# Logstash

create-nginx-index:
	curl --header "content-type: application/JSON" -XPUT http://localhost/elasticsearch/nginx -d "$$(cat logstash/nginx_template.json)"

logstash: network #create-nginx-index
	${DC} -f ${DC_FILE}-logstash.yml up -d

logstash-exec:
	$(DC) -f ${DC_FILE}-logstash.yml exec logstash bash

# backend

# development mode
backend/.env:
	cp backend/.env.sample backend/.env

backend-dev: network backend/.env
	@echo docker-compose up backend for dev
	#@export ${DC} -f ${DC_FILE}.yml up -d $(DC_UP_ARGS) 2>&1 | grep -v orphan
	@export EXEC_ENV=development;${DC} -f ${DC_FILE}.yml up -d $(DC_UP_ARGS)

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
	@echo configuring data downloader
	git clone -b feat/clean-authors https://github.com/victorjourne/IGA-BF.git
	make -C IGA-BF run base_path=$(DATA_PATH)

clean:
	@sudo rm -rf IGA-BF

test:
	$(DC) -f ${DC_FILE}.yml exec -T backend pytest tests/iga/test_app.py::test_healthcheck

##############
#  NGINX     #
##############

nginx-dev: network
	${DC} -f ${DC_FILE}-nginx-dev.yml up -d $(DC_UP_ARGS)
nginx-dev-stop: network
	${DC} -f ${DC_FILE}-nginx-dev.yml down
nginx-dev-exec:
	${DC} -f $(DC_FILE)-nginx-dev.yml exec nginx-dev sh

nginx: network
	${DC} -f $(DC_FILE)-nginx.yml up -d --build
nginx-stop:
	${DC} -f $(DC_FILE)-nginx.yml down

nginx-exec:
	${DC} -f $(DC_FILE)-nginx.yml exec nginx-production sh

nginx-create-user:
	@read -p "Enter User:" user; \
	echo $$user; \
	${DC} -f $(DC_FILE)-nginx.yml exec nginx-production sh -c "touch /etc/nginx/apache2/.htpasswd;htpasswd /etc/nginx/apache2/.htpasswd $$user"



##############
#  Frontend  #
##############

frontend-dev:
	@echo docker-compose run ${APP} frontend dev #--build
	${DC} -f ${DC_FILE}-frontend-dev.yml up -d  $(DC_UP_ARGS)
	$(DC) -f ${DC_FILE}-frontend-dev.yml exec -d frontend-dev npm run dev:tailwindcss

frontend-exec:
	$(DC) -f ${DC_FILE}-frontend-dev.yml exec frontend-dev sh

frontend-dev-stop:
	${DC} -f ${DC_FILE}-frontend-dev.yml down

###############
# Build Stage #
###############

build: frontend-build nginx-build

build-dir:
	@if [ ! -d "$(BUILD_DIR)" ] ; then mkdir -p $(BUILD_DIR) ; fi

build-dir-clean:
	@if [ -d "$(BUILD_DIR)" ] ; then (rm -rf $(BUILD_DIR) > /dev/null 2>&1) ; fi


frontend-check-build:
	${DC} -f $(DC_FILE)-frontend-build.yml config -q

frontend-build-dist:  frontend-check-build
	@echo building ${APP} frontend in ${FRONTEND}
	${DC} -f  $(DC_FILE)-frontend-build.yml  build $(DC_BUILD_ARGS)

$(BUILD_DIR)/$(FILE_FRONTEND_DIST_APP_VERSION): build-dir
	${DC} -f $(DC_FILE)-frontend-build.yml run -T frontend-build sh -c "npm run export > /dev/null 2>&1 && tar czf - __sapper__/export/ -C /app" > $(BUILD_DIR)/$(FILE_FRONTEND_DIST_APP_VERSION)
	#cp $(BUILD_DIR)/$(FILE_FRONTEND_DIST_APP_VERSION) $(BUILD_DIR)/$(FILE_FRONTEND_DIST_LATEST_VERSION)


frontend-build: network frontend-build-dist $(BUILD_DIR)/$(FILE_FRONTEND_DIST_APP_VERSION)

frontend-clean-dist:
	@rm -rf ${FRONTEND}/$(FILE_FRONTEND_APP_VERSION) > /dev/null 2>&1 || true

frontend-clean-dist-archive:
	@rm -rf ${FRONTEND}/$(FILE_FRONTEND_DIST_APP_VERSION) > /dev/null 2>&1 || true
	@rm -rf ${NGINX}/$(FILE_FRONTEND_DIST_APP_VERSION) > /dev/null 2>&1 || true

nginx-check-build:
	${DC} -f $(DC_FILE)-nginx.yml config -q

nginx-build: nginx-check-build
	@echo building ${APP} nginx
	cp $(BUILD_DIR)/$(FILE_FRONTEND_DIST_APP_VERSION) ${NGINX}/
	${DC} -f $(DC_FILE)-nginx.yml build $(DC_BUILD_ARGS)

#############
# SWIFT 	  #
#############
chmod:
	chmod +x swift/*.sh

frontend-upload-swift: chmod
	@echo "Upload ${APP}-build/$(FILE_FRONTEND_DIST_APP_VERSION) to SWIFT BUCKET $(BUCKET_NAME)"
	swift/upload.sh ${BUCKET_NAME} ${APP}-build/$(FILE_FRONTEND_DIST_APP_VERSION) 'curl'

frontend-download-swift: chmod
	@echo "Download $(FILE_FRONTEND_DIST_APP_VERSION) from SWIFT to ${APP}-build"
	swift/download.sh ${BUCKET_NAME} ${APP}-build/$(FILE_FRONTEND_DIST_APP_VERSION) 'curl'

download: chmod
	swift/download.sh $(BUCKET_NAME) $(SRC) 'curl'
upload: chmod
	swift/upload.sh $(BUCKET_NAME) $(SRC) 'curl'

###############
# General 	  #
###############
start: elasticsearch backend-start kibana logstash nginx
stop: nginx-stop backend-stop elasticsearch-stop kibana-stop logstash-stop

dev: network frontend-dev backend-dev elasticsearch kibana nginx-dev
down: frontend-dev-stop backend-dev-stop elasticsearch-stop kibana-stop nginx-dev-stop
