"""
This handler responses to Lex intent searching for documents related to card benefits,
interest rates, or FAQ in Amazon Opensearch
"""
from opensearchpy import OpenSearch, RequestsHttpConnection, AWSV4SignerAuth
import boto3
import dialogstate_utils as dialog
from prompts_responses import Prompts, Responses
import json
import os
import logging

logger = logging.getLogger()

prompts = Prompts('card_services_faq')

host = os.environ['OSENDPOINT']  # Need to remove https in env var For example, my-test-domain.us-east-1.es.amazonaws.com
region = os.environ['AWSREGION']  # e.g. us-west-1

credentials = boto3.Session().get_credentials()
auth = AWSV4SignerAuth(credentials, region)
index_name = 'searchbot'


# ------Helper functions for building response to Lex
def elicitSlot(session_attributes, intent_name, slots, slotToElicit, message):
    return {
        "sessionState": {
            "sessionAttributes": session_attributes,
            "dialogAction": {
                "type": 'ElicitSlot',
                "slotToElicit": slotToElicit,
            },
            "intent": {
                "name": intent_name,
                "slots": slots,
            }
        },
        "messages": [message],
    }


# ------Helper functions
def buildValidationResult(isValid, violatedSlot, messageContent):
    if messageContent is null:
        result = {
            "isValid": isValid,
            "violatedSlot": violatedSlot
        }
    else:
        result = {
            "isValid": isValid,
            "violatedSlot": violatedSlot,
            "message": {
                "contentType": 'PlainText', "content": messageContent
            }
        }
    return json.dumps(result)


def validateKey(keyword):
    # validate available keyword for seaching FAQ
    accept_keywords = ['card benefits', 'card interest rates']
    if keyword in accept_keywords:
        return buildValidationResult(true, null, null)
    else:
        return buildValidationResult(false, keyword, prompts.get('InvalidKeyword'))


def searchKeyword(intent_request):
    intent = dialog.get_intent(intent_request)
    active_contexts = dialog.get_active_contexts(intent_request)
    session_attributes = dialog.get_session_attributes(intent_request)
    slot_keyword = dialog.get_slot('SearchKeyword', intent)
    slots = intent["slots"]

    logger.debug('slot_keywork === {}'.format(slot_keyword))

    invoke_source = intent_request["invocationSource"]
    logger.debug('invocation source === {}'.format(invoke_source))

    if invoke_source == 'DialogCodeHook':
        # Perform basic validation on the supplied input slots.  Use the elicitSlot dialog action to re-prompt for the first violation detected.
        if not slot_keyword:
            elicitSlotUsingLexPrompt(session_attributes, intent["name"], slots, 'Keyword')  # Keyword is the slot types
            logger.debug('Slot keyword is invalid')
            return

        validationResult = validateKey(slot_keyword)
        if not validationResult["isValid"]:
            elicitSlot(session_attributes, intent["name"], slots, validationResult["violatedSlot"],
                       validationResult["message"])
            logger.debug('Search Keyword is not supported')
            return None

    return queryOpensearch(slot_keyword, intent_request)


def queryOpensearch(keyword, intent_request):
    intent = dialog.get_intent(intent_request)
    active_contexts = dialog.get_active_contexts(intent_request)
    session_attributes = dialog.get_session_attributes(intent_request)

    client = OpenSearch(
        hosts=[{'host': host, 'port': 443}],
        http_auth=auth,
        use_ssl=True,
        verify_certs=True,
        connection_class=RequestsHttpConnection
    )
    query = {
        'size': 2,
        'query': {
            'multi_match': {
                'query': keyword,
            }
        }
    }
    response = client.search(
        body=query,
        index=index_name
    )
    search_result = ""

    if response['hits']['total']['value'] > 0:
        search_content = response['hits']['hits'][0]['_source']['attachment']['content']
        filepath = response['hits']['hits'][0]['_source']['filePath']
        prompt_01 = prompts.get('SearchSuccess01')
        prompt_02 = prompts.get('SearchSuccess02')
        search_result = prompt_01 + "\n" + search_content[0:200] + "\n" + prompt_02 + filepath
        # print(search_result)
    else:
        search_result = prompts.get('SearchFailure')

    logger.debug('===Search completed===')
    # return search_result to Lex
    return dialog.close(active_contexts, session_attributes, intent,
                        [{'contentType': 'PlainText', 'content': search_result}])


def handler(intent_request):
    logger.debug('org intent request ===== {}'.format(intent_request))
    return searchKeyword(intent_request)
