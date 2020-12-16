#!/bin/bash

login_guest() {
    wget --post-data='email=&password=' https://www.audiokinetic.com/wwise/launcher/?action=login -O base64jwt.txt

    DWN_SIGNATURE=`cat base64jwt.txt | sed -e 's/.*signature\":"//' | sed -e 's/\".*$//'`
    DWN_PAYLOAD=`cat base64jwt.txt | sed -e 's/.*payload\":"//' | sed -e 's/\".*$//'`

    rm base64jwt.txt

    echo ${DWN_SIGNATURE} > signature64.txt
    echo ${DWN_PAYLOAD} > payload64.txt

    base64 -d signature64.txt > signature.sig
    base64 -d payload64.txt > payload-utf8.txt

    rm signature64.txt payload64.txt

    # TODO: check signature with pub key
    EXTRACTED_JWT=`cat payload-utf8.txt | sed -e 's/.*jwt\":"//' | sed -e 's/\".*$//'`

    echo "${EXTRACTED_JWT}" > jwt.txt

    rm signature.sig payload-utf8.txt
}

test ! -f jwt.txt && login_guest

exit

# The following lines still do not work

wget --no-cookies --header \
"Cookie: jwt=`cat jwt.txt`;\
Range: bytes=0-;\
Content-type: application/json" \
https://www.audiokinetic.com/wwise/launcher/?get=2019.1.10_7250/Wwise_v2019.1.10_Build7250_SDK.Linux.tar.xz

PUBKEY="-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAnAYv/1xDhJ39iT7Ftzcv
zXmhZRHkw5fbMPvz65z0Zh30yZCCmi5RZ0ds5kLcNdov0cdRkhPkWGkWe9/G+dkX
54DRMdvgIcuvmpAgxKz3re1vuTZHvz1DR2sy5FpSPV6lsX3CRLpaXzEo9fgYdqyB
cnqeOaq1byeNTMp2uRUF84NzkH2A3x6Vxx6pThdVMAVKbvPUhEtSBARAKxQstCkQ
ut8FlvQm2RgJrwbmXQfloz4h7uPwaM2jD2eApCfXHK05xh+1zMWFu6oqhqkfKUIK
GceEwONPkd039fwirfgKjbD5iGli3AuNn6PFVqyK0tcG/qYhjNVtJLCsHSmHyipD
rQIDAQAB
-----END PUBLIC KEY-----"
