Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

cd "C:\Users\sirok\MoCKA\transparency\sample05"

if(-not (Test-Path ".\time_target.txt")) { throw "missing time_target.txt" }
if(-not (Test-Path ".\response.tsr")) { throw "missing response.tsr" }
if(-not (Test-Path ".\tsa_cert.pem")) { throw "missing tsa_cert.pem" }

openssl ts -verify -data time_target.txt -in response.tsr -CAfile tsa_cert.pem -untrusted tsa_cert.pem
