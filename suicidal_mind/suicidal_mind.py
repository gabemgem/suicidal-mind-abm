from BPTK_Py import Model
from BPTK_Py import sd_functions as sd
from helpers import round_to_dt
import pandas as pd


def check_in_params(parameters, key, default_value):
    """Check if a key exists in the parameters dictionary, return its value or a default value."""
    return parameters[key] if key in parameters else default_value

class SuicidalMind(Model):
    def __init__(self, name, parameters = {}, rng = None, **kwargs):
        super().__init__(name=name, **kwargs)

        self.rng = rng if rng is not None else None

        # Stocks
        Defeat_Humiliation = self.stock("Defeat_Humiliation")
        Entrapment = self.stock("Entrapment")
        Suicidal_Ideation = self.stock("Suicidal_Ideation")
        Suicidal_Behavior = self.stock("Suicidal_Behavior")

        Life_Events_Effect = self.stock("Life_Events_Effect")
        Capability_From_Planning = self.stock("Capability_From_Planning")
        Time_At_High_Risk = self.stock("Time_At_High_Risk")

        # Flows
        Negative_Cognition = self.flow("Negative_Cognition")
        Defeat_Time_Reduction = self.flow("Defeat_Time_Reduction")
        Defeat_to_Entrapment = self.flow("Defeat_to_Entrapment")
        Entrapment_Time_Reduction = self.flow("Entrapment_Time_Reduction")
        Entrapment_to_Ideation = self.flow("Entrapment_to_Ideation")
        Ideation_Time_Reduction = self.flow("Ideation_Time_Reduction")
        Ideation_to_Behavior = self.flow("Ideation_to_Behavior")
        Behavior_Time_Reduction = self.flow("Behavior_Time_Reduction")

        Life_Events_Triggers = self.flow("Life_Events_Triggers")
        Life_Events_Time_Reduction = self.flow("Life_Events_Time_Reduction")
        Planning = self.flow("Planning")
        Increasing_Time_At_High_Risk = self.flow("Increasing_Time_At_High_Risk")
        Decreasing_Time_At_High_Risk = self.flow("Decreasing_Time_At_High_Risk")

        # Converters
        CAPABILITY = self.converter("CAPABILITY")
        DESIRE = self.converter("DESIRE")
        RISK = self.converter("RISK")
        diathesis = self.converter("diathesis")
        environment = self.converter("environment")
        coping = self.converter("coping")
        normal_event_effect = self.converter("normal_event_effect")
        severe_event_effect = self.converter("severe_event_effect")
        threat_to_self_mod = self.converter("threat_to_self_mod")
        motivational_mod = self.converter("motivational_mod")
        volitional_mod = self.converter("volitional_mod")

        # Constants
        attempt_threshold = self.constant("attempt_threshold")
        coping_init = self.constant("coping_init")
        diathesis_init = self.constant("diathesis_init")
        diathesis_weight = self.constant("diathesis_weight")
        environment_init = self.constant("environment_init")
        environment_weight = self.constant("environment_weight")
        event_decay_rate = self.constant("event_decay_rate")
        event_max_effect = self.constant("event_max_effect")
        high_risk_day_window = self.constant("high_risk_day_window")
        high_risk_volitional_weight = self.constant("high_risk_volitional_weight")
        normal_event_tolerance = self.constant("normal_event_tolerance")
        threat_to_self_characteristics = self.constant("threat_to_self_characteristics")
        motivational_characteristics = self.constant("motivational_characteristics")
        volitional_characteristics = self.constant("volitional_characteristics")
        suicide_death_rate = self.constant("suicide_death_rate")
        time_reduction = self.constant("time_reduction")

        # Other Variables
        self.isHighRisk = False

        # Initial Values
        Defeat_Humiliation.initial_value = check_in_params(parameters, "Defeat_Humiliation", 0.0)
        Entrapment.initial_value = check_in_params(parameters, "Entrapment", 0.0)
        Suicidal_Ideation.initial_value = check_in_params(parameters, "Suicidal_Ideation", 0.0)
        Suicidal_Behavior.initial_value = check_in_params(parameters, "Suicidal_Behavior", 0.0)

        Life_Events_Effect.initial_value = check_in_params(parameters, "Life_Events_Effect", 0.0)
        Capability_From_Planning.initial_value = check_in_params(parameters, "Capability_From_Planning", 0.0)
        Time_At_High_Risk.initial_value = check_in_params(parameters, "Time_At_High_Risk", 0.0)

        # Equations
        Defeat_Humiliation.equation = Negative_Cognition - Defeat_Time_Reduction
        Entrapment.equation = Defeat_to_Entrapment - Defeat_Time_Reduction
        Suicidal_Ideation.equation = Entrapment_to_Ideation - Ideation_Time_Reduction
        Suicidal_Behavior.equation = Ideation_to_Behavior - Behavior_Time_Reduction

        Life_Events_Effect.equation = Life_Events_Triggers - Life_Events_Time_Reduction
        Capability_From_Planning.equation = Planning
        Time_At_High_Risk.equation = Increasing_Time_At_High_Risk - Decreasing_Time_At_High_Risk

        Negative_Cognition.equation = (
            0.4 * (Life_Events_Effect * diathesis * environment)
        ) + (
            0.4 * (Life_Events_Effect * diathesis * environment * (
                Entrapment + Suicidal_Ideation + Suicidal_Behavior
                ) / 3.0
            )
        ) + (
            diathesis * diathesis_weight
        ) + (
            environment * environment_weight
        ) # TODO: Left out universal relief

        Defeat_Time_Reduction.equation = Defeat_Humiliation * time_reduction # TODO: Left out defeat/humiliation interv.
        Defeat_to_Entrapment.equation = threat_to_self_mod * Defeat_Humiliation
        Entrapment_Time_Reduction.equation = Entrapment * time_reduction # TODO: Left out entrapment interv.
        Entrapment_to_Ideation.equation = motivational_mod * Entrapment
        Ideation_Time_Reduction.equation = Suicidal_Ideation * time_reduction # TODO: Left out ideation interv.
        Ideation_to_Behavior.equation = volitional_mod * Suicidal_Ideation
        Behavior_Time_Reduction.equation = Suicidal_Behavior * time_reduction # TODO: Left out behavior interv.

        Life_Events_Triggers.equation = 0.0 # TODO: Figure out how to introduce life events
        Life_Events_Time_Reduction.equation = event_max_effect * Life_Events_Effect
        Planning.equation = 0.0 #TODO: Figure out how to introduce planning
        Increasing_Time_At_High_Risk.equation = sd.If(self.isHighRisk and Time_At_High_Risk < high_risk_day_window, 1.0, 0.0)
        Decreasing_Time_At_High_Risk.equation = sd.If(Time_At_High_Risk>0 and not self.isHighRisk, 1, 0)

        CAPABILITY.equation = volitional_mod * 100
        DESIRE.equation = Suicidal_Ideation
        RISK.equation = 0.4 * Suicidal_Behavior + sd.If(self.isHighRisk, 0.5 * attempt_threshold, 0.0)
        diathesis.equation = diathesis_init # TODO: Left out diathesis interv.
        environment.equation = environment_init # TODO: Left out environment interv.
        coping.equation = coping_init # TODO: Left out way to change coping
        normal_event_effect.equation = event_max_effect * (1 - normal_event_tolerance) * (1 - coping)
        severe_event_effect.equation = event_max_effect * (1 - coping)
        threat_to_self_mod.equation = (threat_to_self_characteristics + (1-coping)) / 2.0 # TODO: Add each tts component
        motivational_mod.equation = motivational_characteristics # TODO: Add each motivational component
        volitional_mod.equation = (
            (high_risk_volitional_weight * sd.If(high_risk_day_window != 0,
                Time_At_High_Risk / high_risk_day_window, 0.0)) +
            (Capability_From_Planning / 10.0) +
            volitional_characteristics
        ) / 4.0 # TODO: Add each volitional component and possible interventions?

        attempt_threshold.equation = check_in_params(parameters, "attempt_threshold", 100.0)
        coping_init.equation = check_in_params(parameters, "coping_init", 0.1)
        diathesis_init.equation = check_in_params(parameters, "diathesis_init", 0.5)
        diathesis_weight.equation = check_in_params(parameters, "diathesis_weight", 20.0)
        environment_init.equation = check_in_params(parameters, "environment_init", 0.5)
        environment_weight.equation = check_in_params(parameters, "environment_weight", 20.0)
        event_decay_rate.equation = check_in_params(parameters, "event_decay_rate", 0.5)
        event_max_effect.equation = check_in_params(parameters, "event_max_effect", 50.0)
        high_risk_day_window.equation = check_in_params(parameters, "high_risk_day_window", 50.0)
        high_risk_volitional_weight.equation = check_in_params(parameters, "high_risk_volitional_weight", 0.2)
        normal_event_tolerance.equation = check_in_params(parameters, "normal_event_tolerance", 0.5)
        threat_to_self_characteristics.equation = check_in_params(parameters, "threat_to_self_characteristics",
                                                                       0.1)
        motivational_characteristics.equation = check_in_params(parameters, "motivational_characteristics", 0.1)
        volitional_characteristics.equation = check_in_params(parameters, "volitional_characteristics", 0.1)
        suicide_death_rate.equation = check_in_params(parameters, "suicide_death_rate", 0.03)
        time_reduction.equation = check_in_params(parameters, "time_reduction", 0.2)

        # Events
        self.events = []

        # Runner variable that can step all variables through time
        _runner = self.converter("_runner")
        _runner.equation = eval(f'({" + ".join([eq for eq in self.memo.keys() if eq != "_runner"])}) * 0.0')

        # Initialize everything to time = 0
        self.t = 0
        self.evaluate_equation("_runner", self.t)
        self.process_events()


    def __getitem__(self, item):
        """
        Get the value of a stock, flow, converter, or constant by its name at the current time step.

        Args:
            item (str): The name of the stock, flow, converter, or constant.
        Returns:
            float: The value of the specified item at the current time step.
        Raises:
            KeyError: If the item is not found.
        """
        if item not in self.memo:
            raise KeyError(f"Item '{item}' not found in the model.")
        if self.t not in self.memo[item]:
            raise KeyError(f"Item '{item}' not found at time step {self.t}.")
        return self.memo[item][self.t]

    def process_change(self, change):
        """
        Process a change in the model's state.

        Args:
            change (dict): A dictionary containing the changes to be applied.
        """
        if "isHighRisk" in change:
            self.isHighRisk = change["isHighRisk"]

        for key, value in change.items():
            if key == "isHighRisk":
                continue
            if key in self.memo:
                self.memo[key][self.t] = value
            else:
                raise KeyError(f"Key '{key}' not found in the model.")

    def register_event(self, event):
        """
        Register an event to be processed on time steps.

        Args:
            event (Event): The event to register.
        """
        event.model = self
        self.events.append(event)

    def process_events(self):
        """
        Process all events that are scheduled to occur at the current time step.
        This method checks each event and activates it if its next occurrence matches the current time.
        """
        for event in self.events:
            event_change = event.activate(self)
            if event_change:
                self.process_change(event_change)

    def step(self):
        """
        Step the model forward by one time unit, updating all stocks, flows, converters, and constants.
        """
        self.t = round_to_dt(self, self.t+self.dt)
        self.evaluate_equation("_runner", self.t)

        self.process_events()

    def step_to(self, time):
        while self.t < time:
            self.step()

    def df(self):
        """
        Returns the current state of the model as a pandas dataframe
        :return: A pandas dataframe
        """
        df = pd.DataFrame(self.memo)
        return df.drop("_runner", axis=1)





