#!/bin/sh
# Boundary proof, run inside the container (no token needed). Prints PASS/FAIL lines.
ok(){ if eval "$2" >/dev/null 2>&1; then echo "FAIL $1"; else echo "PASS $1 (blocked)"; fi; }
if echo x > /work/inside.txt; then echo "PASS write inside worktree"; else echo "FAIL write inside"; fi
ok "write to /" "echo x > /evil"
ok "overwrite /work/.git (ro nested mount)" "echo x > /work/.git"
ok "write via ../" "echo x > /work/../evil"
ok "write to /usr" "echo x > /usr/evil"
ok "write main checkout" "echo x > /e/Github/Orgs/omi-teams/omi-squad2/evil"
ok "write host .git common dir" "echo x > /e/Github/Orgs/omi-teams/omi-squad2/.git/evil"
ok "write /proc/sys" "echo 1 > /proc/sys/kernel/hostname"
ok "mount tmpfs" "mount -t tmpfs none /mnt"
ok "exec in /tmp (noexec)" "cp /bin/true /tmp/t && /tmp/t"
[ -e /var/run/docker.sock ] && echo "FAIL docker.sock present" || echo "PASS no docker socket"
echo "uid=$(id -u) caps=$(grep CapEff /proc/self/status) $(grep NoNewPrivs /proc/self/status)"
echo "mounts:"; grep -E ' /work | / ' /proc/self/mountinfo | cut -d' ' -f5,6
