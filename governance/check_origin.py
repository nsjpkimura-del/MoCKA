import subprocess
import sys

EXPECTED = "git@github.com:nsjpkimura-del/MoCKA.git"

def run(cmd):
    return subprocess.check_output(cmd, shell=True).decode().strip()

origin = run("git remote get-url origin")
status = run("git status --porcelain")

if origin != EXPECTED:
    print("origin mismatch")
    sys.exit(1)

if status != "":
    print("working tree not clean")
    sys.exit(1)

print("origin and working tree OK")
