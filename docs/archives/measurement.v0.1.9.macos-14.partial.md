# Measurement evidence (T-1-a partial) — macos-14

- Run: 25371652043
- Date: 2026-05-05T10:42:14Z
- Arch: ARM64
- OS: macOS macos-14
- install_exit: 0
- stdout_degraded: 0
- state_degraded: 0
- Q1.5_result: PASS

## install.py output (truncated)
```
[install] Rendered plist written: /Users/runner/Library/LaunchAgents/com.teamwork-leader.auto-resume-daemon.plist
[install] Running: launchctl bootstrap gui/501 /Users/runner/Library/LaunchAgents/com.teamwork-leader.auto-resume-daemon.plist
[install] launchctl bootstrap succeeded.
[install] Wrote install probe: /Users/runner/work/teamwork-leader/teamwork-leader/.teamlead-project/.teamlead/install-probe.json (probe_id=56cb9637-ee95-42b5-b337-afbcd74510d7)
[install] Polling for pong at /Users/runner/work/teamwork-leader/teamwork-leader/.teamlead-project/.teamlead/install-probe.pong.json (timeout=10s)...

[install] WARNING: Daemon installed but install-probe pong not received within 10s.
[install] The daemon may take a moment to start. Installation is considered complete.

[install] Installation complete.
```

## launchctl print output (if PASS)
```
gui/501/com.teamwork-leader.auto-resume-daemon = {
	active count = 0
	path = /Users/runner/Library/LaunchAgents/com.teamwork-leader.auto-resume-daemon.plist
	type = LaunchAgent
	state = spawn scheduled

	program = /usr/bin/env
	arguments = {
		/usr/bin/env
		python3
		/Users/runner/work/teamwork-leader/teamwork-leader/scripts/daemon.py
		--watch
		/Users/runner/work/teamwork-leader/teamwork-leader/.teamlead-project/.teamlead/
	}

	working directory = /Users/runner/work/teamwork-leader/teamwork-leader/.teamlead-project

	stdout path = /Users/runner/work/teamwork-leader/teamwork-leader/.teamlead-project/.teamlead/daemon.out
	stderr path = /Users/runner/work/teamwork-leader/teamwork-leader/.teamlead-project/.teamlead/daemon.err
	inherited environment = {
		SSH_AUTH_SOCK => /private/tmp/com.apple.launchd.XUotmpFBj2/Listeners
	}

	default environment = {
		PATH => /usr/bin:/bin:/usr/sbin:/sbin
	}

	environment = {
		CLAUDE_PLUGIN_ROOT => /Users/runner/work/teamwork-leader/teamwork-leader
		CLAUDE_PROJECT_DIR => /Users/runner/work/teamwork-leader/teamwork-leader/.teamlead-project
		TEAMLEAD_DAEMON_VERSION => v0.1.7
		XPC_SERVICE_NAME => com.teamwork-leader.auto-resume-daemon
	}

	domain = gui/501 [100003]
	asid = 100003
	minimum runtime = 10
	exit timeout = 5
	runs = 2
	last exit code = 1

	semaphores = {
		successful exit => 0
	}

	event triggers = {
		com.apple.launchd.WatchPaths => {
			keepalive = 0
			service = com.teamwork-leader.auto-resume-daemon
			stream = com.apple.fsevents.matching
			monitor = com.apple.UserEventAgent-Aqua
			descriptor = {
				"WatchPaths" => [
					0 = "/Users/runner/work/teamwork-leader/teamwork-leader/.teamlead-project/.teamlead/"
				]
			}
		}
	}

	event channels = {
		"com.apple.fsevents.matching" = {
			port = 0x3521b
			active = 0
			managed = 1
			reset = 0
			hide = 0
			watching = 0
		}
	}

	spawn type = daemon (3)
	jetsam priority = 40
	jetsam memory limit (active) = (unlimited)
	jetsam memory limit (inactive) = (unlimited)
	jetsamproperties category = daemon
	jetsam thread limit = 32
	cpumon = default
	probabilistic guard malloc policy = {
		activation rate = 1/1000
		sample rate = 1/0
	}

	properties = runatload | inferred program | system service | tle system
}
```
