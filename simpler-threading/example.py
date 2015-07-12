import threading
ldd_con = threading.Event()


class DgmsService(threading.Thread):

    def __init__(self, mode, pre_config=False):
        self.ps = PubsubManager(...)
        self.time_step = 5
        self.dynamic_update_period = 300
        threading.Thread.__init__(self, name="dgms_service")

    def publish_dgms_status(self):
        # read and publish some state from the DB
        self.ps.pub(status)

    def update_dynamic_setpoints(self, ...):
        # solve and publish updated dynamic setpoints
        result = Solver.solve().withAlgorithm(algoType)
        self.ps.pub(result)

    def shutoff_inverters(self):
       # assign which inverters to shutoff
       self.ps.pub(zero_setpoints)

    def dgms_sub_thread(self):
        # Publishes dgms_status on MBS and checks the violation of lower deadband
        last_publish_time = 0.0
        while True:
            if time.time()-last_publish_time > self.time_step:
                self.publish_dgms_status(cumulative_setpoint=aggr_setpoint)
                last_publish_time = time.time()
            time.sleep(0.5)
            current_net_load = # read passively from some external class or variable
            if (current_net_load < self.pcc_import_band[1]):
                ldd_con.set()
            else:
                ldd_con.clear()

    def run(self):
        counter = 0
        acquiesce = 1
        latest_turn_off = 0.0
        chk_deadband = threading.Thread(name='dgms_sub_thread', target=self.dgms_sub_thread)
        chk_deadband.setDaemon(True)
        chk_deadband.start()
        while True:
            try:
                if ldd_con.is_set() and (time.time() - latest_turn_off > self.dynamic_update_period/2):
                    self.shutoff_inverters()
                    latest_turn_off = time.time()
                if (not ldd_con.is_set()) & (counter % acquiesce == 0):
                    acquiesce = 1
                    if counter % (self.dynamic_update_period/self.time_step) == 0:
                        self.update_dynamic_setpoints(...)
                        latest_turn_off = 0.0
            except Exception, err:
                acquiesce += 1
                logging.exception("Caught exception in DgmsService thread: %s", err)
            if not ldd_con.is_set():
                counter += 1
                time.sleep(self.time_step)
