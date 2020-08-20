export APP = browser
export APP_PATH := $(shell pwd)
export APP_VERSION	:= 0.1
export DATA_PATH = ${APP_PATH}/backend/tests/iga/data
#export APP_VERSION	:= $(shell git describe --tags || cat VERSION )

# docker compose
export DC := /usr/local/bin/docker-compose
export DC_DIR=${APP_PATH}
export DC_FILE=${DC_DIR}/docker-compose
export DC_PREFIX := $(shell echo ${APP} | tr '[:upper:]' '[:lower:]' | tr '_' '-')
export DC_NETWORK := $(shell echo ${APP} | tr '[:upper:]' '[:lower:]')
export DC_BUILD_ARGS = --pull --no-cache

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

# BACKEND dir
export BACKEND=${APP_PATH}/backend
export BACKEND_PORT=5000
export BACKEND_HOST = ${APP}-backend

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

# traefik
export TRAEFIK_PATH=${APP_PATH}/traefik
export LOG_LEVEL=DEBUG

# this is usefull with most python apps in dev mode because if stdout is
# buffered logs do not shows in realtime
PYTHONUNBUFFERED=1

dummy		    := $(shell touch artifacts)
include ./artifacts


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

backend-dev: network backend/.env
	@echo docker-compose up backend for dev
	#@export ${DC} -f ${DC_FILE}.yml up -d --build --force-recreate 2>&1 | grep -v orphan
	@export EXEC_ENV=development;${DC} -f ${DC_FILE}.yml up -d --build #--force-recreate

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
	make -C IGA-BF run base_path=$(BACKEND)/tests/iga/data

clean:
	@sudo rm -rf IGA-BF

test:
	$(DC) -f ${DC_FILE}.yml exec -T backend pytest tests/iga/test_app.py::test_healthcheck

##############
#  NGINX     #
##############

nginx-dev: network
	${DC} -f ${DC_FILE}-nginx-dev.yml up -d --build --force-recreate
nginx-dev-stop: network
	${DC} -f ${DC_FILE}-nginx-dev.yml down

nginx: nginx-build network
	${DC} -f $(DC_FILE)-nginx.yml up -d
nginx-stop:
	${DC} -f $(DC_FILE)-nginx.yml down

nginx-exec:
	${DC} -f $(DC_FILE)-nginx.yml exec nginx-production sh

##############
#  Frontend  #
##############


frontend-dev:
	@echo docker-compose run ${APP} frontend dev #--build
	${DC} -f ${DC_FILE}-frontend-dev.yml up -d  #--build --force-recreate
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

${FRONTEND}/$(FILE_FRONTEND_APP_VERSION):
	( cd ${FRONTEND} && tar -zcvf $(FILE_FRONTEND_APP_VERSION) __sapper__/export/  )

frontend-check-build:
	${DC} -f $(DC_FILE)-frontend-build.yml config -q

frontend-build-dist: ${FRONTEND}/$(FILE_FRONTEND_APP_VERSION) frontend-check-build
	@echo building ${APP} frontend in ${FRONTEND}
	${DC} -f  $(DC_FILE)-frontend-build.yml  build $(DC_BUILD_ARGS)

$(BUILD_DIR)/$(FILE_FRONTEND_DIST_APP_VERSION): build-dir
	${DC} -f $(DC_FILE)-frontend-build.yml run -T --rm frontend-build  sh  -c "npm run export > /dev/null 2>&1 && tar czf - __sapper__/export/ -C /app" > $(BUILD_DIR)/$(FILE_FRONTEND_DIST_APP_VERSION)
	cp $(BUILD_DIR)/$(FILE_FRONTEND_DIST_APP_VERSION) $(BUILD_DIR)/$(FILE_FRONTEND_DIST_LATEST_VERSION)


frontend-build: network frontend-build-dist $(BUILD_DIR)/$(FILE_FRONTEND_DIST_APP_VERSION)

frontend-clean-dist:
	@rm -rf ${FRONTEND}/$(FILE_FRONTEND_APP_VERSION) > /dev/null 2>&1 || true

frontend-clean-dist-archive:
	@rm -rf ${FRONTEND}/$(FILE_FRONTEND_DIST_APP_VERSION) > /dev/null 2>&1 || true
	@rm -rf ${NGINX}/$(FILE_FRONTEND_DIST_APP_VERSION) > /dev/null 2>&1 || true

frontend-export:
	${DC} -f $(DC_FILE)-frontend-build.yml config -q



nginx-check-build:
	${DC} -f $(DC_FILE)-nginx.yml config -q

nginx-build: nginx-check-build
	@echo building ${APP} nginx
	cp $(BUILD_DIR)/$(FILE_FRONTEND_DIST_APP_VERSION) ${NGINX}/
	${DC} -f $(DC_FILE)-nginx.yml build $(DC_BUILD_ARGS)


###############
# General 	  #
###############
start: elasticsearch backend-start nginx
stop: nginx-stop backend-stop elasticsearch-stop

dev: network frontend-dev backend-dev elasticsearch nginx-dev
down: frontend-dev-stop backend-dev-stop elasticsearch-stop nginx-dev-stop

#############
# SWIFT 	  #
#############
chmod:
	chmod +x openstack/*.sh

frontend-upload-swift:
	@echo "Send ${APP}-build/$(FILE_FRONTEND_DIST_APP_VERSION) to SWIFT"
	# swift --insecure --debug --os-auth-token $(OS_AUTH_TOKEN) --os-storage-url $(OS_STORAGE_URL) upload ${APP} ${APP}-build/"$(FILE_FRONTEND_DIST_APP_VERSION)"
	./openstack/upload.sh ${APP} ${APP}-build/"$(FILE_FRONTEND_DIST_APP_VERSION)" 'swift'

frontend-download-swift: chmod
	./openstack/download.sh ${APP} ${APP}-build/$(FILE_FRONTEND_DIST_APP_VERSION) 'curl'

data-upload-swift: chmod
	./openstack/upload.sh ${APP} backend/tests/iga/data 'swift'
