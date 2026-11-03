#!/bin/bash
# Setup static WiFi IP + SSH for wireless access
# Run once on the Raspberry Pi: sudo bash setup_wifi_ssh.sh MyHotspot 172.20.10.9 172.20.10.1 28

set -e

WIFI_SSID="${1:?usage: sudo bash setup_wifi_ssh.sh <ssid> <static-ip> <gateway> [prefix-len]}"
STATIC_IP="${2:?usage: sudo bash setup_wifi_ssh.sh <ssid> <static-ip> <gateway> [prefix-len]}"
GATEWAY="${3:?usage: sudo bash setup_wifi_ssh.sh <ssid> <static-ip> <gateway> [prefix-len]}"
SUBNET="${4:-24}"
PI_USER="${SUDO_USER:-student}"
DNS="8.8.8.8,1.1.1.1"

echo "=== Setting static IP $STATIC_IP on WiFi ==="

nmcli connection modify "$WIFI_SSID" \
    ipv4.method manual \
    ipv4.addresses "$STATIC_IP/$SUBNET" \
    ipv4.gateway "$GATEWAY" \
    ipv4.dns "$DNS"

nmcli connection up "$WIFI_SSID"

echo "=== Making sure SSH is enabled and running ==="
systemctl enable ssh
systemctl start ssh

echo ""
echo "=== Done! ==="
echo ""
echo "Pi is now reachable at:"
echo "  IP:       $STATIC_IP"
echo "  Hostname: $(hostname).local  (via mDNS, same network only)"
echo ""
echo "Connect from any device:"
echo "  ssh $PI_USER@$STATIC_IP"
echo "  ssh $PI_USER@$(hostname).local"
echo ""
echo "=== To add SSH key from a new device, run on that device: ==="
echo "  ssh-copy-id $PI_USER@$STATIC_IP"
echo "  OR paste your public key into /home/$PI_USER/.ssh/authorized_keys"
