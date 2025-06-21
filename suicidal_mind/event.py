from helpers import round_to_dt

class Event:
    def __init__(self, name, action, trigger_type="timeout", trigger_params={}):
        """
        Initialize an Event object.

        :param name: Name of the event.
        :param action: Action to be executed when the event is triggered. This should be a
            callable (function) that takes no arguments and returns a dict of model values to change.
        :param trigger_type: Type of the trigger (default is "timeout"). Options are:
            - "timeout": Triggered after a specified time period.
            - "condition": Triggered when a specific condition is met.
            - "rate": Triggered based on an exponential distribution rate.
        :param trigger_params: Dict of parameters for the trigger. Options are:
            - For "timeout": {"first_occurrence": float, "recurrence_time": float(optional)}
            - For "condition": {"condition": callable} - a function that takes no arguments and returns a boolean indicating if the condition is met.
            - For "rate": {"first_occurerence": float(optional), "rate": float} - rate for the exponential distribution.
        """
        self.name = name
        self.action = action
        self.trigger_type = trigger_type
        self.trigger_params = trigger_params
        self.check_trigger_params()

        self.model = None
        self.first_occurrence = trigger_params.get("first_occurrence", 0.0)
        self.next_occurrence = None if trigger_type == "condition" else self.first_occurrence

    def activate(self):
        """
        Check if the event should be activated, call the event action, and initialize the next occurrence time.
        If the model is not set, raise a ValueError.
        :raises ValueError: If the model is not set before activating the event.
        :return: A dict of model values to change as a result of the event action or None.
        """
        if self.model is None:
            raise ValueError("Model must be set before activating the event.")

        if self.trigger_type == "condition" and not self.trigger_params["condition"]():
            return None
        if self.next_occurrence is None or self.next_occurrence > self.model.time:
            return None
        # Call the action and get the changes to the model
        changes = self.action()

        if self.trigger_type == "timeout":
            self.next_occurrence = self.next_occurrence + self.trigger_params["recurrence_time"] if (
                    "recurrence_time" in self.trigger_params) else None
        elif self.trigger_type == "condition":
            self.next_occurrence += self.model.dt
        elif self.trigger_type == "rate":
            # add a draw from an exponential distribution to the next occurrence time rounded to the model's dt
            self.next_occurrence += round_to_dt(self.model,
                                                self.model.rng.exponential(self.trigger_params["rate"]))

        return changes

    def check_trigger_params(self):
        """
        Check if the trigger parameters are valid based on the trigger type.

        :raises ValueError: If the trigger parameters are not valid for the specified trigger type.
        """
        if self.trigger_type == "timeout":
            if "first_occurrence" not in self.trigger_params:
                raise ValueError("Trigger parameters for 'timeout' must include 'first_occurrence'.")
            if "recurrence_time" in self.trigger_params and self.trigger_params["recurrence_time"] <= 0:
                raise ValueError("Recurrence time must be greater than 0 for 'timeout' events.")
        elif self.trigger_type == "condition":
            if "condition" not in self.trigger_params or not callable(self.trigger_params["condition"]):
                raise ValueError("Trigger parameters for 'condition' must include a callable 'condition'.")
        elif self.trigger_type == "rate":
            if "rate" not in self.trigger_params or self.trigger_params["rate"] <= 0:
                raise ValueError("Trigger parameters for 'rate' must include a positive 'rate'.")
            if "first_occurrence" in self.trigger_params and self.trigger_params["first_occurrence"] < 0:
                raise ValueError("First occurrence time must be non-negative for 'rate' events.")
