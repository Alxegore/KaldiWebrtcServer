FROM debian:testing
MAINTAINER Danijel Koržinek <danijel.korzinek@pja.edu.pl>

RUN apt clean && \
    rm -rf /var/lib/apt/lists/* && \apt-get -y update && \
            apt-get install -y python3 python3-pip git libavdevice-dev libavfilter-dev libopus-dev libvpx-dev pkg-config --fix-missing &&\
            apt-get clean && apt-get autoclean

RUN pip3 install aiortc aiohttp numpy
RUN bash -c 'echo -e ...'
RUN git clone https://github.com/Alxegore/KaldiWebrtcServer /server

ENTRYPOINT ["python3","/server/server.py"]
CMD ["--servers","/server/servers.json"]
