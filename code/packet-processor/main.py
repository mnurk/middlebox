import asyncio
from nats.aio.client import Client as NATS
import os
import random
from scapy.all import Ether, IP, IPOption, UDP
import time
import json
import statistics
import math

delays = []
rtts = []
covert_log = []

ENABLE_COVERT = os.getenv("ENABLE_COVERT", "0") == "1"
COVERT_MESSAGE = os.getenv("COVERT_MESSAGE", "HELLO")
COVERT_INDEX = 0

def inject_covert_data(packet):
    global COVERT_INDEX
    if not packet.haslayer(IP):
        return packet

    ip_layer = packet[IP]
    msg_bytes = COVERT_MESSAGE.encode()

    if COVERT_INDEX >= len(msg_bytes):
        return packet

    char = msg_bytes[COVERT_INDEX]
    COVERT_INDEX += 1

    ts_value = char << 24
    option = IPOption()
    option.option = 68
    option.length = 8
    option.data = ts_value.to_bytes(4, 'big')

    ip_layer.options = [option]
    ip_layer.len = None
    ip_layer.chksum = None

    packet[IP] = ip_layer
    covert_log.append({
        "char": chr(char),
        "ascii": char,
        "ts_value": ts_value,
        "index": COVERT_INDEX,
        "timestamp": time.time()
    })
    return packet

def calculate_statistics(data_list):
    if not data_list:
        return {"avg": 0, "ci_95": 0}
    avg = statistics.mean(data_list)
    if len(data_list) < 2:
        return {"avg": avg, "ci_95": 0}
    stdev = statistics.stdev(data_list)
    ci_95 = 1.96 * stdev / math.sqrt(len(data_list))
    return {"avg": avg, "ci_95": ci_95}

def calculate_channel_capacity():
    if len(covert_log) < 2:
        return 0
    start = covert_log[0]["timestamp"]
    end = covert_log[-1]["timestamp"]
    duration = end - start
    bits_sent = 8 * len(covert_log)
    return bits_sent / duration if duration > 0 else 0

async def run():
    nc = NATS()
    nats_url = os.getenv("NATS_SURVEYOR_SERVERS", "nats://nats:4222")
    await nc.connect(nats_url)

    async def message_handler(msg):
        subject = msg.subject
        data = msg.data
        packet = Ether(data)
        receive_time = time.time()

        if ENABLE_COVERT and packet.haslayer(IP):
            try:
                packet = inject_covert_data(packet)
                data = bytes(packet)
            except Exception as e:
                print("Covert injection error:", e)

        mean_delay = float(os.getenv("MEAN_DELAY", 5e-6))
        delay = random.expovariate(1 / mean_delay)
        delays.append(delay)
        await asyncio.sleep(delay)

        forward_time = time.time()
        rtt = forward_time - receive_time
        rtts.append(rtt)

        if subject == "inpktsec":
            await nc.publish("outpktinsec", data)
        else:
            await nc.publish("outpktsec", data)

    await nc.subscribe("inpktsec", cb=message_handler)
    await nc.subscribe("inpktinsec", cb=message_handler)

    print("Covert packet processor running...")
    try:
        while True:
            await asyncio.sleep(1)
            save_logs()
    except KeyboardInterrupt:
        print("Shutting down...")
        await nc.close()
        save_logs()

def save_logs():
    rtt_stats = calculate_statistics(rtts)
    delay_stats = calculate_statistics(delays)
    channel_capacity = calculate_channel_capacity() if ENABLE_COVERT else 0

    results = {
        "rtts": rtts,
        "delays": delays,
        "rtt_avg": rtt_stats["avg"],
        "rtt_ci_95": rtt_stats["ci_95"],
        "delay_avg": delay_stats["avg"],
        "delay_ci_95": delay_stats["ci_95"],
        "covert_channel_capacity_bps": channel_capacity
    }

    with open("results.json", "w") as f:
        json.dump(results, f, indent=2)

    if ENABLE_COVERT:
        with open("covert_log.json", "w") as f:
            json.dump(covert_log, f, indent=2)

if __name__ == '__main__':
    asyncio.run(run())
