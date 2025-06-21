
def round_to_dt(model, value):
    """
    Round a value to the model's time step (dt).

    :param value: The value to be rounded.
    :return: The rounded value.
    """
    return round(value / model.dt) * model.dt