FROM python:3.6

# Prepare
ENV KEEPER_HOME /usr/src/keeper

# Create working dir
RUN mkdir -p /usr/src/keeper
WORKDIR /usr/src/keeper

#Copy project
COPY . .

# Install
RUN python3 -m pip install -r requirements.txt

RUN chmod 755 /usr/src/keeper/bin/keeper.sh
ENTRYPOINT [ "/usr/src/keeper/bin/keeper.sh" ]