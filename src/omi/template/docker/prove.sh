#!/bin/sh
# Boundary proof, run inside the container (no token needed): python -m omi worker <wt> --prove
ok(){ if eval "$2" >/dev/null 2>&1; then echo "FAIL $1"; else echo "PASS $1 (blocked)"; fi; }
if echo x > /work/inside.txt; then echo "PASS write inside worktree"; rm /work/inside.txt; else echo "FAIL write inside"; fi
ok "write to /" "echo x > /evil"
ok "overwrite /work/.git (ro nested mount)" "echo x > /work/.git"
ok "write via ../" "echo x > /work/../evil"
ok "write to /usr" "echo x > /usr/evil"
ok "write /proc/sys" "echo 1 > /proc/sys/kernel/hostname"
ok "mount tmpfs" "mount -t tmpfs none /mnt"
ok "exec in /tmp (noexec)" "cp /bin/true /tmp/t && /tmp/t"
[ -e /var/run/docker.sock ] && echo "FAIL docker.sock present" || echo "PASS no docker socket"
# network: CONNECT through the egress proxy (HTTPS_PROXY), direct TCP must fail
px=${HTTPS_PROXY#http://}
connect(){ python3 -c 'import socket,sys
h,p=sys.argv[1].rsplit(":",1)
s=socket.create_connection((h,int(p)),10)
s.sendall(("CONNECT %s:443 HTTP/1.1\r\nHost: %s:443\r\n\r\n"%(sys.argv[2],sys.argv[2])).encode())
print(s.recv(4096).decode(errors="replace").split("\r\n")[0])' "$px" "$1" 2>&1; }
r=$(connect api.anthropic.com)
case "$r" in *" 200 "*) echo "PASS allowed host api.anthropic.com connects ($r)";; *) echo "FAIL allowed host api.anthropic.com: $r";; esac
r=$(connect example.com)
case "$r" in *" 403 "*example.com*network_allow*) echo "PASS blocked host example.com fails ($r)";; *) echo "FAIL blocked host example.com: $r";; esac
ok "direct TCP to 1.1.1.1:443 (no proxy)" "python3 -c 'import socket;socket.create_connection((\"1.1.1.1\",443),5)'"
# CLIs in the image reach their API host through the proxy: a bogus key must give an auth error, not a network one
cli(){ out=$(HOME=/home/node timeout 90 "$@" 2>&1 </dev/null | tail -c 600)
  if echo "$out" | grep -qiE 'ENOTFOUND|EAI_AGAIN|ECONNREFUSED|timed out|dns|network|proxy|403 forbidden|error sending request'; then echo "FAIL $n: network error: $out"
  elif echo "$out" | grep -qiE '401|unauthorized|authentication|invalid|incorrect api key|api key'; then echo "PASS $n reaches its API through the proxy (auth error)"
  else echo "FAIL $n: unexpected output: $out"; fi; }
n="claude CLI"; ANTHROPIC_API_KEY=sk-ant-prove-invalid cli claude -p hi
n="codex CLI"; OPENAI_API_KEY=sk-prove-invalid cli codex exec --skip-git-repo-check hi
echo "uid=$(id -u) caps=$(grep CapEff /proc/self/status) $(grep NoNewPrivs /proc/self/status)"
echo "mounts:"; grep -E ' /work | / ' /proc/self/mountinfo | cut -d' ' -f5,6
