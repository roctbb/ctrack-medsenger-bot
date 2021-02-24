from ctrack_bot import *
from apscheduler.schedulers.background import BlockingScheduler


scheduler = BlockingScheduler()
scheduler.add_job(tasks, 'interval', minutes=5)
scheduler.start()