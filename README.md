<div align="center">

# Omarchy Plugin

**Omarchy shell plugins, published and kept current from one place.**

Install the whole suite with one command, and every improvement lands on your
machine automatically.

</div>

---

## Install

```bash
git clone https://github.com/Omarchy-plugin/myles-omarchy-plugins.git
cd myles-omarchy-plugins
./install.sh
```

That installs the plugins, turns off the stock Omarchy widgets they replace, and
enables automatic updates. To pick a subset:

```bash
./install.sh --only myles.clock,myles.network
```

Prefer one plugin at a time? Every repo below installs on its own:

```bash
omarchy plugin add https://github.com/Omarchy-plugin/myles-clock.git --enable --yes
```

## The suite

| Plugin | Version | Replaces | What it does |
| --- | --- | --- | --- |
| [myles-clock](./myles-clock) | 1.0.0 | `omarchy.clock` | Calendar clock with merged world-clock places, holiday markers, custom formats |
| [myles-network](./myles-network) | 2.9.0 | `omarchy.network` | Subnet warnings, resilient IPv4 recovery, profile backups, usage totals, Proton VPN |
| [myles-agents](./myles-agents) | 1.3.0 | `omarchy.agents` | Every installed coding agent ranked by token usage, with trends and one-click launch |
| [omarchy-myles-media](./omarchy-myles-media) | 1.12.1 | `omarchy.media` | Media hub: Spotify, YouTube, Radio Garden, local files, video PiP, downloads, casting |
| [myles-usage](./myles-usage) | 1.4.0 | — | Active/idle tracking, searchable reports, goals, focus insights, timers |
| [myles-appearance-picker](./myles-appearance-picker) | 2.0.0 | — | Grouped theme and wallpaper picker |

[myles-omarchy-plugins](./myles-omarchy-plugins) is the installer and updater itself.

## Updates are automatic

An improvement pushed here reaches installed machines without you running
anything. Three layers, so a fix lands whether or not the machine is awake:

| Trigger | When it runs |
| --- | --- |
| systemd user timer | Every 30 minutes, with jitter; catches up after sleep |
| `post-update.d` hook | After an Omarchy system update |
| `post-boot.d` hook | After boot |
| `omarchy plugin update --yes` | Whenever you want it, on demand |

Updates are a `git fetch` plus a fast-forward. Each plugin folder is
re-validated after merging and **rolled back automatically** if validation
fails, then the shell rescans — so new code is live without a logout, and a bad
push cannot leave you with a broken shell.

Check on it:

```bash
systemctl --user list-timers myles-plugin-update.timer
systemctl --user status myles-plugin-update.service
omarchy-myles-plugin-update          # run it now, by hand
```

Log: `~/.local/state/omarchy/myles-plugin-update.log`

The updater only touches plugins whose id starts with `myles.`, so third-party
plugins you installed from elsewhere are never updated without you asking.

## What these plugins reach out to

Every plugin documents its own external commands, network calls, and privilege
boundaries in its README. In summary:

| Plugin | Network |
| --- | --- |
| `myles-clock` | None at runtime. Weather links are plain clickable `wttr.in` URLs |
| `myles-network` | `ping.archlinux.org` (NetworkManager's probe); `api.ipify.org` for public IP, **off by default** |
| `myles-calculator` | `open.er-api.com` for live FX rates, only in currency mode |
| `omarchy-myles-media` | YouTube, Radio Garden, and cast receivers, as the features require |
| `myles-agents`, `myles-usage`, `myles-appearance-picker`, `myles-workspaces` | None |

`myles-agents` and `myles-usage` keep all data on your machine and upload
nothing. Usage history lives in `~/.local/state/omarchy/`, outside the plugin
folder, so it survives uninstall and reinstall.

## Security

**Omarchy plugins run unsandboxed** inside the long-lived `omarchy-shell`
process, with your user permissions and no isolation. A plugin can read your
files and run commands as you.

That means:

- Install only from repos you trust, and read the source before enabling it.
- Prefer a plugin with a short, auditable history over a large opaque one.
- The automatic updater is a real supply-chain surface. It pulls from this
  organisation over HTTPS and fast-forwards only, so an update can never
  silently discard your local copy — but a compromised publish key could ship
  code to every machine running the suite. `--no-hooks` at install time turns
  the updater off if you would rather update by hand.

## Contributing

Fixes and improvements are welcome.

1. Edit the plugin in place, at `~/.config/omarchy/plugins/<id>/`. Saved
   changes reload automatically; force rediscovery with
   `omarchy-shell shell rescanPlugins`.
2. Run the tests where they exist (`myles-clock` and `myles-network` have node
   suites) and check the folder:

   ```bash
   omarchy plugin validate ~/.config/omarchy/plugins/<id>
   ```

3. Commit, tag a version bump in `manifest.json`, and push. The updater
   delivers it.

**A local edit inside a plugin folder blocks that plugin's own update**, because
the updater fast-forwards only. Commit and push your work, or the suite stalls
on it.

Conventions for a new plugin:

- Prefix the id with `myles.` — that prefix is what scopes the auto-updater.
  Never use `omarchy.*`; that namespace belongs to Omarchy.
- One plugin per repository, named after the id with dots as dashes
  (`myles.clock` → `myles-clock`).
- `manifest.json` must carry `author: "Mylesoft"` and a `license`.
- If it derives from an Omarchy built-in, keep the `omarchy.clonedFrom` field,
  and **retain the upstream copyright in `LICENSE`**. Omarchy is MIT © David
  Heinemeier Hansson, and MIT requires the notice to survive in copies.
- Document every external command, network call, and privilege boundary in the
  README.

## Credits

Built for [Omarchy](https://omarchy.org) by [Mylesoft](https://github.com/Mylesoft).

- Omarchy — MIT, © David Heinemeier Hansson. `myles-clock`, `myles-network`,
  `myles-agents`, `myles-workspaces`, and `myles-media` are forks of Omarchy's
  built-in plugins and retain its copyright.
- Plugin authors and contributors — see each repository.
