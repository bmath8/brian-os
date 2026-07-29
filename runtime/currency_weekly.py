#!/usr/bin/env python3
"""currency_weekly.py - thin wrapper so cron can run the WEEKLY deep-dive.

hermes cron --script takes no args, so this just sets --weekly and calls the agent.
Schedule this Sundays off-peak; currency_agent.py (no args) is the cheap daily job.
"""
import os, sys
sys.argv.append("--weekly")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import currency_agent
currency_agent.main()
