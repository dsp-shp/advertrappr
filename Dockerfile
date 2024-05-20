FROM python:3.11-slim

ENV AVITO_URL ""
ENV CIAN_URL ""
ENV YANDEX_URL ""
ENV DISPOSE 7
ENV REPEAT 90
ENV MESSENGER "{}"

RUN apt update 
RUN apt install -fy wget git 
RUN wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
RUN apt install -fy ./google-chrome*.deb

RUN pip install --upgrade pip 
RUN pip install git+https://github.com/dsp-shp/advertrappr.git
RUN advertrappr config -m ${MESSENGER}

ENTRYPOINT ["/bin/sh", "-c", "advertrappr run -a ${AVITO_URL} -c ${CIAN_URL} -y ${YANDEX_URL} -d ${DISPOSE} -r ${REPEAT}"]
