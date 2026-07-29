# G18 — Make the fleet survive a reboot (super simple, ~5 min)

**What this does, in plain English:** right now your agent "gateway" only stays alive
because you're logged in and a startup script restarts it. This change hands the
gateway to Windows-Linux's built-in service manager (systemd) so it **auto-restarts
itself and survives a full reboot** — even before you log in.

**Why you have to do it (not the assistant):** one command needs your password
(`sudo`), and the installer asks a question that needs a real keyboard. The assistant
can't type your password. Everything below is copy-paste.

> ⚠️ Before you start: you'll need your **Ubuntu password** (the one you set the first
> time you opened Ubuntu — NOT your Windows login). If you don't remember it, do
> **Step 0** first. If you do remember it, skip to Step 1.

---

## Step 0 (only if you forgot your Ubuntu password)
1. Press the **Windows key**, type **Ubuntu**, open it.
2. You're now in the black terminal. We'll reset the password. In a *separate*
   regular Windows PowerShell window, run this (sets you to admin so you can reset):
   - Press **Windows key**, type **PowerShell**, click it.
   - Paste: `wsl -d Ubuntu -u root passwd mathe`
   - It says "New password:" — type a new password (you won't see it typing), Enter,
     type it again, Enter. Done — that's your new Ubuntu password. Remember it.

---

## Step 1 — Open the Ubuntu terminal
1. Press the **Windows key**.
2. Type **Ubuntu**.
3. Click the **Ubuntu** app. A black window opens with a prompt like `mathe@... $`.

That black window is where every command below goes. **Type one line, press Enter,
wait until the `$` prompt comes back, then do the next one.**

---

## Step 2 — Install the service
Copy this line, paste it in (right-click pastes in the terminal), press **Enter**:

```
hermes gateway install
```

- It may ask a **yes/no question** (something like "install service? [Y/n]").
  Just type **y** and press **Enter**.
- Wait until you see the `$` prompt again. ✅

---

## Step 3 — Make it run even before you log in (this is the password step)
Paste this, press **Enter**:

```
sudo loginctl enable-linger mathe
```

- It will say **`[sudo] password for mathe:`**
- Type your **Ubuntu password** and press **Enter**.
  👉 **The screen shows NOTHING while you type the password — no dots, no stars.
  That's normal.** Just type it and hit Enter.
- Back to the `$` prompt = ✅ done.

---

## Step 4 — Switch over to the new service
This stops the old hand-started gateway and starts the managed one. Paste each line,
press Enter, wait for the `$` after each:

```
hermes gateway stop
```
```
pkill -f 'venv/bin/hermes gateway run'
```
(That second line might say "no process found" — totally fine.)

```
hermes gateway start
```

---

## Step 5 — Check it worked
Paste this, press Enter:

```
hermes gateway status
```

✅ **Good** = you see something like **`running`** / **`active`**.
❌ If it says not running, go to "If something breaks" below.

Then the real test: **on your phone, message @CK08Bot** (say "hi"). If it replies in
a minute or so, you're done. 🎉

---

## If something breaks (get back to working in 15 seconds)
Paste these two lines:

```
hermes gateway stop
```
```
bash ~/.hermes/start_gateway_if_down.sh
```

That restarts the gateway the old reliable way. Then message the assistant and tell it
what the screen said — we'll sort it out. You won't lose anything; your fleet is safe.

---

## When it's working — tell the assistant
Say: **"G18 done — linger is on."** The assistant will then do a one-time real reboot
test to confirm the fleet comes back by itself, and mark G18 + reboot-survival fully
closed.
