ARG BUILD_FROM
FROM $BUILD_FROM
# lang
ENV LANG C.UTF-8
# shell
SHELL ["/bin/bash", "-o", "pipefail", "-c"]
# install keeper
WORKDIR /opt/keeper
# install required software
RUN echo "[$(date '+%d/%m/%Y %H:%M:%S') - INFO] installing required software"
RUN apk add --no-cache python3 python3-venv python3-pip git
# clone repo
RUN echo "[$(date '+%d/%m/%Y %H:%M:%S') - INFO] getting latest keeper"
RUN git clone --depth 1 -b master https://github.com/nragon/keeper.git ./tmp && \
    mv ./tmp/* . && \
    rm -rf ./tmp && \
    rm -rf ./tests && \
    rm -rf ./setup
# install requirements
RUN python3 -m pip install -r requirements.txt
# copy options
RUN cp /data/options.json ./config/keeper.json
# change permissions
RUN chmod a+x /opt/keeper/bin/keeper
CMD [ "/opt/keeper/bin/keeper" ]
# build arguments
ARG BUILD_ARCH
ARG BUILD_VERSION
ARG BUILD_DATE
ARG BUILD_REF
# labels
LABEL \
    io.hass.name="Keeper" \
    io.hass.description="A service to monitor and maintaining MQTT and HomeAssistant" \
    io.hass.arch="${BUILD_ARCH}" \
    io.hass.type="addon" \
    io.hass.version=${BUILD_VERSION} \
    maintainer="Nuno Gonçalves <nunoo_7@hotmail.com>" \
    org.label-schema.description="A service to monitor and maintaining MQTT and HomeAssistant" \
    org.label-schema.build-date=${BUILD_DATE} \
    org.label-schema.name="Keeper" \
    org.label-schema.schema-version="0.1.2" \
    org.label-schema.url="https://github.com/nragon/keeper" \
    org.label-schema.usage="https://github.com/nragon/keeper/README.md" \
    org.label-schema.vcs-ref=${BUILD_REF} \
    org.label-schema.vcs-url="https://github.com/nragon/keeper" \
    org.label-schema.vendor="Keeper Hass.io Add-on"