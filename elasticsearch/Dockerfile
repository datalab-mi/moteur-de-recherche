ARG ES_VERSION
FROM docker.elastic.co/elasticsearch/elasticsearch:${ES_VERSION}
ADD elasticsearch.yml /usr/share/elasticsearch/config
RUN bin/elasticsearch-plugin install analysis-icu
EXPOSE 9200
