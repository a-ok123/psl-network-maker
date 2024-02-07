import time
import functools


def execution_timer(func):
    """A decorator that prints how long a function took to run.

    Args:
        func (callable): The function to time.

    Returns:
        callable: The wrapped function.
    """

    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        # Before calling the function
        start_time = time.time()

        # Call the function
        result = await func(*args, **kwargs)

        # After the function call
        end_time = time.time()

        # Calculate and print the execution time
        print(f"'{func.__name__}' function took {end_time - start_time} secs to run.")

        return result

    return wrapper
