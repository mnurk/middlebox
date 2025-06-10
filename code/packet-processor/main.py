import asyncio
from nats.aio.client import Client as NATS
import os
import random
from scapy.all import Ether, IP, IPOption, UDP
import time
import json
import statistics
import math
import numpy as np
from collections import deque

class CovertChannelDetector:
    def __init__(self, window_size=100):
        self.window_size = window_size
        self.packet_history = deque(maxlen=window_size)
        self.detection_results = {
            'true_positives': 0,
            'true_negatives': 0,
            'false_positives': 0,
            'false_negatives': 0
        }
        self.last_detection_time = time.time()
        print("CovertChannelDetector initialized")
        
    def detect_ip_option(self, packet):
        if not packet.haslayer(IP):
            return False
        ip_layer = packet[IP]
        if hasattr(ip_layer, 'options'):
            for option in ip_layer.options:
                if isinstance(option, IPOption) and option.option == 68:
                    print("Detected IP timestamp option")
                    return True
        return False
        
    def detect_timing_pattern(self, packet, timestamp):
        if len(self.packet_history) < 2:
            self.packet_history.append((packet, timestamp))
            return False
            
        last_packet_time = self.packet_history[-1][1]
        iat = timestamp - last_packet_time
        
        mean_delay = float(os.getenv("MEAN_DELAY", 5e-6))
        if abs(iat - mean_delay) < mean_delay * 0.1:
            print(f"Detected suspicious timing pattern: IAT={iat}, mean_delay={mean_delay}")
            return True
            
        self.packet_history.append((packet, timestamp))
        return False
        
    def update_detection_results(self, is_covert, detected):
        if is_covert and detected:
            self.detection_results['true_positives'] += 1
            print("True positive detection")
        elif not is_covert and not detected:
            self.detection_results['true_negatives'] += 1
            print("True negative detection")
        elif not is_covert and detected:
            self.detection_results['false_positives'] += 1
            print("False positive detection")
        elif is_covert and not detected:
            self.detection_results['false_negatives'] += 1
            print("False negative detection")
            
    def calculate_metrics(self):
        total = sum(self.detection_results.values())
        if total == 0:
            return {
                'accuracy': 0.0,
                'precision': 0.0,
                'recall': 0.0,
                'f1_score': 0.0,
                'true_positives': 0,
                'true_negatives': 0,
                'false_positives': 0,
                'false_negatives': 0
            }
            
        tp = self.detection_results['true_positives']
        tn = self.detection_results['true_negatives']
        fp = self.detection_results['false_positives']
        fn = self.detection_results['false_negatives']
        
        accuracy = (tp + tn) / total
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
        
        return {
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1_score': f1,
            'true_positives': tp,
            'true_negatives': tn,
            'false_positives': fp,
            'false_negatives': fn
        }

delays = []
rtts = []
covert_log = []
detector = CovertChannelDetector()

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
    print(f"Connecting to NATS at {nats_url}")
    try:
        await nc.connect(nats_url)
        print("Successfully connected to NATS")
    except Exception as e:
        print(f"Failed to connect to NATS: {e}")
        return

    async def message_handler(msg):
        subject = msg.subject
        data = msg.data
        print(f"Received message on subject: {subject}")
        try:
            packet = Ether(data)
            receive_time = time.time()
            print(f"Processed packet: {packet.summary()}")

            if ENABLE_COVERT and packet.haslayer(IP):
                try:
                    packet = inject_covert_data(packet)
                    data = bytes(packet)
                    print("Injected covert data into packet")
                except Exception as e:
                    print("Covert injection error:", e)

            ip_detection = detector.detect_ip_option(packet)
            timing_detection = detector.detect_timing_pattern(packet, receive_time)
            is_detected = ip_detection or timing_detection
            
            detector.update_detection_results(ENABLE_COVERT, is_detected)

            mean_delay = float(os.getenv("MEAN_DELAY", 5e-6))
            delay = random.expovariate(1 / mean_delay)
            delays.append(delay)
            await asyncio.sleep(delay)

            forward_time = time.time()
            rtt = forward_time - receive_time
            rtts.append(rtt)
            print(f"Packet forwarded with RTT: {rtt}")

            if subject == "inpktsec":
                await nc.publish("outpktinsec", data)
                print("Published to outpktinsec")
            else:
                await nc.publish("outpktsec", data)
                print("Published to outpktsec")
        except Exception as e:
            print(f"Error processing packet: {e}")

    print("Subscribing to NATS subjects...")
    await nc.subscribe("inpktsec", cb=message_handler)
    await nc.subscribe("inpktinsec", cb=message_handler)

    print("Covert packet processor and detector running...")
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
    detection_metrics = detector.calculate_metrics()

    results = {
        "rtts": rtts,
        "delays": delays,
        "rtt_avg": rtt_stats["avg"],
        "rtt_ci_95": rtt_stats["ci_95"],
        "delay_avg": delay_stats["avg"],
        "delay_ci_95": delay_stats["ci_95"],
        "covert_channel_capacity_bps": channel_capacity,
        "detection_metrics": detection_metrics
    }

    with open("results.json", "w") as f:
        json.dump(results, f, indent=2)

    if ENABLE_COVERT:
        with open("covert_log.json", "w") as f:
            json.dump(covert_log, f, indent=2)

if __name__ == '__main__':
    asyncio.run(run())
