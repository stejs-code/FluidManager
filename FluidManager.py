import json
import time


def now():
    return time.ticks_ms()


class FluidManager:
    def __init__(self, pump, button, weight):
        self.time_of_last_interaction = 0
        self.full_load_delay = 5000

        self.now = int(round(time.time() * 1000))
        self.button = button
        self.pump = pump
        self.weight = weight

        self.time_of_first_interaction = 0
        self.previous_button = False
        self.action_of_this_round = None
        self.message_of_previous_round = None
        self.pump.low()

        self.glasses = json.load(open("glasses.json"))

        self.weight.tare()
        self.weight.set_gain(128)
        self.weight.set_time_constant(0.7)

        print("waiting for the weight to tare")
        while True:
            self.weight.tare()
            print(self.get_weight_value())
            if self.get_weight_value() == 0:
                print("weight tared successfully")
                break
            time.sleep(0.1)

        self.message = "init completed"

    def new_glass(self):
        # get weight of the glass
        print("getting weight of the glass...")
        weight_of_glass = self.get_stable_weight(1.5)

        # light signalization

        print("started pouring fluid...")
        self.pump.high()
        start_time = now()

        print("waiting for input to stop pouring fluid...")
        while True:
            if self.button.value():
                print("stopping pump")
                self.pump.low()
                end_time = now()
                break

        print("saving new glass: ")

        new_glass = {
            "time": end_time - start_time,
            "weight": weight_of_glass
        }
        getattr(self, 'glasses')[weight_of_glass] = new_glass
        print(getattr(self, 'glasses')[weight_of_glass])

        print("writing to database...")
        f = open("glasses.json", "w")
        f.write(json.dumps(self.glasses))
        f.close()

        print("waiting for glass to be removed")

        while True:
            if self.get_weight_value() == 0:
                print("successfully completed glass creation")
                break

    def fill_glass(self, weight):
        if str(weight) in self.glasses:
            glass = self.glasses[str(weight)]
            start_time = now()
            total_time = glass["time"]
            print("starting pump...")
            self.pump.high()

            while True:
                if (now() - total_time) < start_time:
                    print("deactivating the pump")
                    self.pump.low()
                    print("enjoy your drink ;)")
                    break
                time.sleep(0.01)

    def new_round(self):

        # button hold / full load
        if self.button.value() and self.previous_button:
            if (self.now - self.time_of_first_interaction) > self.full_load_delay:
                self.pump.high()
                self.action_of_this_round == "full_load"
                self.message = "activating the pump, because of long button press..."
                return
            self.message = "waiting to start full load process..."

        # double click / create new glass
        if self.button.value() and not self.previous_button:
            if (self.now - self.time_of_last_interaction) < 600:
                self.action_of_this_round = "glass_creation"
                self.new_glass()

        # stable weight / fill glass
        if self.get_weight_value() != 0:
            self.fill_glass(self.get_stable_weight())

        if not self.message:
            self.message = "deactivating the pump, because of no activity"
        self.action_of_this_round = None
        self.pump.low()

    def start(self):
        while True:
            # print(self.get_weight_value())
            self.now = now()

            self.new_round()

            if not self.button.value() and self.previous_button and not (self.action_of_this_round == "full_load"):
                self.time_of_last_interaction = now()

            if not self.previous_button and self.button.value():
                self.time_of_first_interaction = now()

            if self.message_of_previous_round != self.message:
                print(self.message)

            self.previous_button = self.button.value()
            self.message_of_previous_round = self.message
            self.message = False

            time.sleep(0.1)

    def get_stable_weight(self, accuracy=1.1, timeout=10):
        previous_value = 0
        time_of_start = now()
        while True:
            print(self.get_weight_value())
            if (previous_value == self.get_weight_value()) and (self.get_weight_value() > 0):
                time.sleep(accuracy)
                if previous_value == self.get_weight_value():
                    weight_of_glass = self.get_weight_value()
                    print("weight is now stable, weight of glass is " + str(weight_of_glass) + " g")
                    return weight_of_glass

            if (now() - time_of_start) > (timeout * 1000):
                return False
            previous_value = self.get_weight_value()
            time.sleep(0.2)

    def get_weight_value(self):
        return round(self.weight.read_lowpass() / 1735)
