FROM python:3.12.9

RUN apt-get update && apt-get install -y libpcap-dev python3-dev && apt-get clean && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip && \
    pip install scapy nats-py matplotlib ping3

ENV ENABLE_COVERT=1
ENV COVERT_MESSAGE=HELLO_WORLD
        
WORKDIR /code/packet-processor

COPY . .

RUN python -c "import scapy; print('Scapy installed successfully')"

CMD ["python", "main.py"]
