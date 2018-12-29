# dockerfile for hassio addon
# copyright: © 2018 by Nuno Gonçalves
# license: MIT, see LICENSE for more details.

ARG BUILD_FROM
FROM $BUILD_FROM
# lang
ENV LANG C.UTF-8
# shell
SHELL ["/bin/bash", "-o", "pipefail", "-c", "-e"]
# install keeper
WORKDIR /opt/keeper
# variables for print
ARG NC="\e[0m"
ARG GREEN="\e[1;32m"
ARG RED="\e[1;31m"
ARG TICK="[${GREEN}✓${NC}]"
ARG INFO="[i]"
ARG DONE="${GREEN} done!${NC}"
ARG OVER="\\r\\033[K"
# install required software
RUN printf "  %b installing required software..." "${INFO}"
RUN apk add --no-cache python3 python3-venv python3-pip git > /dev/null
RUN printf "%b  %b required software installed\\n" "${OVER}" "${TICK}"
# clone repo
RUN printf "  %b downloading keeper repo..." "${INFO}"
RUN git clone --depth 1 -b master https://github.com/nragon/keeper.git ./tmp > /dev/null && \
    rm -rf ./tmp/tests && \
    rm -rf ./tmp/setup && \
    mv ./tmp/* . && \
    rm -rf ./tmp
RUN printf "%b  %b keeper repo downloaded\\n" "${OVER}" "${TICK}"
# install requirements
RUN printf "  %b creating virtual environment..." "${INFO}"
RUN python3 -m pip install -r requirements.txt > /dev/null
RUN printf "%b  %b virtual environment\\n" "${OVER}" "${TICK}"
# copy options
RUN printf "  %b configuring properties..." "${INFO}"
RUN cp /data/options.json ./config/keeper.json
RUN printf "%b  %b properties configured\\n" "${OVER}" "${TICK}"
# change permissions
RUN printf "  %b enabling keeper..." "${INFO}"
RUN chmod a+x /opt/keeper/bin/keeper
CMD [ "/opt/keeper/bin/keeper" ]
RUN printf "%b  %b keeper enabled\\n" "${OVER}" "${TICK}"
RUN printf "%b" "${DONE}\\n"
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