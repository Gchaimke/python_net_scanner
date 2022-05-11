import argparse
import csv
from dataclasses import dataclass
from datetime import datetime
from os import path
import pathlib
import re
import subprocess

PROJECT_PATH = pathlib.Path(__file__).parent
MAC_DBS = path.join(PROJECT_PATH, "mac_dbs.csv")


@dataclass
class MyDevice:
    ip: str = ""
    mac: str = ""
    vendor: str = ""
    hostname: str = ""


class NetScanner():

    def __init__(self, start_ip: str = "192.168.1.1", end_ip: str = "",  **kwargs):
        self.start_ip = start_ip
        self.end_ip = end_ip if end_ip != "" else self.start_ip

    def run(self) -> list:
        self.check_range()
        devices = self.identefy_devices()
        print('IP', '\t'*2, 'MAC', '\t'*3, 'Vendor', '\t'*5, 'HOSTNAME')
        for device in devices:
            print(
                f"{device.ip}\t{device.mac}\t{device.vendor:<45}\t{device.hostname}")
        return devices

    @staticmethod
    def get_vendor(mac: str) -> dict:
        mac = mac.replace('-', '').replace(':', '')
        with open(MAC_DBS, encoding='utf-8') as csvfile:
            mac_reader = csv.DictReader(csvfile, delimiter=',')
            for row in mac_reader:
                if mac.upper() in row.get('MAC'):
                    return row.get('VENDOR')
        return "NA"

    @staticmethod
    def get_hostname(ip):
        response = subprocess.run(f"nslookup {ip}", capture_output=True)
        row_host = response.stdout.decode('utf-8')
        arp_regex = re.compile(r"Name:\W+(.+)", re.MULTILINE)
        hostname = re.findall(arp_regex, row_host)
        if hostname:
            return hostname[0]

        return ip

    @staticmethod
    def ping(ip: str) -> str:
        response = subprocess.run(
            f"ping {ip} -n 1 -w 2000", capture_output=True)
        return response.stdout.decode('utf-8')

    @staticmethod
    def get_arps() -> str:
        response = subprocess.run(f"arp -a", capture_output=True)
        row_arp = response.stdout.decode('utf-8')
        arp_regex = re.compile(
            r"(\d+\.\d+\.\d+.\d+)\W+((\w+-\w+-\w+)-\w+-\w+-\w+)\W+dynamic", re.MULTILINE)
        arp_table = re.findall(arp_regex, row_arp)
        return arp_table

    def identefy_devices(self) -> list:
        foo = []
        arp_table = self.get_arps()
        for line in arp_table:
            if len(line) > 2:
                device = MyDevice()
                device.ip = line[0]
                device.hostname = self.get_hostname(device.ip)
                device.mac = line[1]
                device.vendor = self.get_vendor(line[2])
                foo.append(device)
        return foo

    @staticmethod
    def append_line_to_db(line: dict, filename="new_db.csv") -> None:
        with open(filename, 'a', encoding='utf-8') as file:
            file.write('MAC,VENDOR\n')
            _mac = line.get('MAC')
            _vendor = line.get('VENDOR')
            new_line = f"{_mac.replace('-','')},{_vendor}\n"
            file.write(new_line)

    @staticmethod
    def get_range(source_range: str, stop_ip: str = '') -> list:
        oct_range = source_range.split(maxsplit=4, sep=".")
        oct_stop = stop_ip.split(
            maxsplit=4, sep=".") if stop_ip != '' else oct_range
        if len(oct_range) > 3 and len(oct_stop) > 3:
            ip_range = [f"{a}.{b}.{c}.{d}" for a in range(int(oct_range[0]), int(oct_stop[0])+1, 1)
                        for b in range(int(oct_range[1]), int(oct_stop[1])+1, 1)
                        for c in range(int(oct_range[2]), int(oct_stop[2])+1, 1)
                        for d in range(int(oct_range[3]), int(oct_stop[3])+1, 1)]
            return ip_range
        else:
            return list(source_range)

    def check_range(self):
        range = self.get_range(self.start_ip, self.end_ip)
        print("Discovering", end="")
        start = datetime.now()
        for ip in range:
            print(".", end="")
            self.ping(ip)
        total = datetime.now() - start
        print("\nTotal time", total)


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--startip',required=True)
    parser.add_argument('-e', '--endip')
    args = parser.parse_args()

    if not args.endip:
        start_ip = end_ip = args.startip
    else:
        start_ip = args.startip
        end_ip = args.endip

    app = NetScanner(start_ip=start_ip, end_ip=end_ip)
    app.run()
