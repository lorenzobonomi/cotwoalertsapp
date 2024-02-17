import logging
import azure.functions as func
from airthingsAPI import getAirThings

app = func.FunctionApp()

@app.schedule(
    schedule = '0 */40 * * * *', 
    arg_name = 'myTimer', 
    run_on_startup = True,
    use_monitor=False
)

def airthings(myTimer: func.TimerRequest) -> None:

    # Call function to send viewplus events
    getAirThings()
    
    if myTimer.past_due:
        logging.info('Timer past due')

    logging.info('Timer executed.')

    