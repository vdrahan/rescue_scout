#!/bin/bash
# Setup static WiFi IP + SSH for wireless access
# Run once on the Raspberry Pi: sudo bash setup_wifi_ssh.sh

set -e

WIFI_SSID="Vlad"
STATIC_IP="172.20.10.9"
SUBNET="28"
GATEWAY="172.20.10.1"
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
echo "  ssh student@$STATIC_IP"
echo "  ssh student@$(hostname).local"
echo ""
echo "=== To add SSH key from a new device, run on that device: ==="
echo "  ssh-copy-id student@$STATIC_IP"
echo "  OR paste your public key into /home/student/.ssh/authorized_keys"
