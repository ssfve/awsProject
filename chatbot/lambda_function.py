"""
This code sample demonstrates an implementation of the Lex Code Hook Interface
in order to serve a bot which manages banking account services. Bot, Intent,
and Slot models which are compatible with this sample can be found in the
Lex Console as part of the 'CardServices' template.
"""

import json
import datetime
import time
import os
import dateutil.parser
import logging
import dialogstate_utils as dialog
import repeat
import make_card_payment
import fallback
import card_services_FAQ
import report_missing_card
import authenticate
import check_balance

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


# --- Main handler & Dispatch ---

def dispatch(intent_request):
    """
    Route to the respective intent module code
    """
    intent = dialog.get_intent(intent_request)
    intent_name = intent['name']
    session_id = intent_request['sessionId']
    bot_id = intent_request['bot']['id']
    bot_alias_id = intent_request['bot']['aliasId']
    dialog.set_session_attribute(intent_request, 'sessionId', session_id)
    session_attributes = dialog.get_session_attributes(intent_request)
    active_contexts = dialog.get_active_contexts(intent_request)

    # Default dialog state is set to delegate
    next_state = dialog.delegate(active_contexts, session_attributes, intent)

    if intent_name == 'FallbackIntent':
        return fallback.handler(intent_request)

    # Dispatch to the respective bot's intent handlers
    if intent_name == 'CardAuth':
        next_state = authenticate.handler(intent_request)
    if intent_name == 'CheckBalance':
        next_state = check_balance.handler(intent_request)
    if intent_name == 'PayCardBill':
        next_state = make_card_payment.handler(intent_request)
    if intent_name == 'CardServicesFAQ':
        next_state = card_services_FAQ.handler(intent_request)
    if intent_name == 'ReportMissingCard':
        next_state = report_missing_card.handler(intent_request)
    if intent_name == 'Repeat':
        next_state = repeat.handler(intent_request)

    return next_state


def lambda_handler(event, context):
    """
    Route the incoming request based on intent.
    The JSON body of the request is provided in the event slot.
    """
    # By default, treat the user request as coming from the America/New_York time zone.
    os.environ['TZ'] = 'America/New_York'
    time.tzset()
    # logger.debug('event.bot.name={}'.format(event['bot']['name']))

    return dispatch(event)
