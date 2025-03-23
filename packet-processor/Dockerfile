FROM python:3.12

RUN pip install --upgrade pip && \
    pip install scapy nats-py matplotlib ping3

WORKDIR /code/packet-processor

COPY . .

RUN python -c "import matplotlib.pyplot as plt; print('matplotlib installed successfully')"
RUN python -c "import ping3; print('ping3 installed successfully')"

CMD ["python", "main.py"]