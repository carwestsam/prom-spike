from mongo_sender import Metric, MetricList, Sender
import time
import random
import os
import math

if __name__ == '__main__':
    time.sleep(4)
    pending_orders = Metric('pending_orders', 123, {'prop':'0.1'})
    accepted_orders = Metric('accepted_orders', 23, {'prop':'0.2'})
    failed_orders = Metric('failed_orders', 19, {'prop': '0.3'})
    
    instanceProps = {'ip': os.getenv('ip', '127.0.0.1'), 'env': os.getenv('env', 'local')}

    metrics = MetricList([pending_orders, accepted_orders, failed_orders], instanceProps)
    sender = Sender(os.getenv('mongo_host', 'localhost'), int(os.getenv('mongo_port','27017')))

    TOTAL = 1200
    t = random.randint(0, 10)
    while True:
        time.sleep(2)

        t += 1
        
        pending = (t % 10) * 10
        rest = TOTAL - pending
        accepted = int(500 * math.sin(t / 10.0) + 500)
        failed = rest - accepted

        print("pending: %d\naccepted: %d\nfailed: %d\n---\n\n" % (pending, accepted, failed))

        # update info
        pending_orders.set_value(pending)
        accepted_orders.set_value(accepted)
        failed_orders.set_value(failed)
        
        sender.update(metrics)
